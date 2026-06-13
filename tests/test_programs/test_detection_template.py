from unittest.mock import Mock

import pytest
from celery import Celery
from celery.contrib.testing.worker import TestWorkController

from acoupi import data
from acoupi.components import SqliteStore
from acoupi.components.audio_recorder import MicrophoneConfig
from acoupi.components.types import Model
from acoupi.programs.templates import (
    AudioConfiguration,
    DetectionProgram,
    DetectionProgramConfiguration,
    DetectionsConfiguration,
    MessagingConfig,
    PathsConfiguration,
)


class Config(DetectionProgramConfiguration):
    name: str = "Test Program"


@pytest.fixture
def detection_config() -> DetectionsConfiguration:
    return DetectionsConfiguration(threshold=0.4)


@pytest.fixture
def config(
    audio_config: AudioConfiguration,
    paths_config: PathsConfiguration,
    microphone_config: MicrophoneConfig,
    messaging_config: MessagingConfig,
    detection_config: DetectionsConfiguration,
) -> Config:
    return Config(
        name="test",
        paths=paths_config,
        microphone=microphone_config,
        messaging=messaging_config,
        recording=audio_config,
        detections=detection_config,
    )


@pytest.mark.usefixtures("celery_app")
def test_can_initialise_program(
    celery_app: Celery,
    config: Config,
):
    model = Mock()

    class Program(DetectionProgram):
        config_schema = Config

        def configure_model(self, config):
            return model

    Program(config, celery_app)


@pytest.mark.usefixtures("celery_app")
def test_program_check_runs_all_relevant_checks(
    celery_app: Celery,
    config: Config,
):
    model = Mock()
    messenger = Mock()
    recorder = Mock()

    class Program(DetectionProgram):
        config_schema = Config

        def configure_model(self, config):
            return model

        def configure_messenger(self, config):
            return messenger

        def configure_recorder(self, config):
            return recorder

    program = Program(config, celery_app)

    program.check(config)
    model.check.assert_called_once()
    recorder.check.assert_called_once()
    messenger.check.assert_called_once()


@pytest.mark.usefixtures("celery_app")
def test_program_has_all_required_tasks(
    celery_app: Celery,
    config: Config,
):
    model = Mock()

    class Program(DetectionProgram):
        config_schema = Config

        def configure_model(self, config):
            return model

    program = Program(config, celery_app)

    assert "recording_task" in program.tasks
    assert "file_management_task" in program.tasks
    assert "detection_task" in program.tasks
    assert "heartbeat_task" in program.tasks
    assert "send_messages_task" in program.tasks


class MockModel(Model):
    name: str = "test_model"

    def run(self, recording: data.Recording) -> data.ModelOutput:
        return data.ModelOutput(
            name_model="test",
            recording=recording,
            detections=[
                data.PresenceDetection(
                    detection_score=score / 10,
                    tags=[
                        data.PredictedTag(
                            tag=data.Tag(
                                key="species", value="Myotis daubentonii"
                            ),
                            confidence_score=score2 / 10,
                        )
                        for score2 in range(11)
                    ],
                )
                for score in range(11)
            ],
        )


def test_worker_config_has_dedicated_detection_worker():
    worker_config = DetectionProgram.worker_config
    assert worker_config is not None
    workers = {w.name: w for w in worker_config.workers}
    assert "detection" in workers, (
        "DetectionProgram must declare a 'detection' worker"
    )
    assert workers["detection"].concurrency == 1, (
        "detection worker must have concurrency=1 to prevent OOM from parallel model loads"
    )
    assert workers["recording"].concurrency == 1, (
        "recording worker must have concurrency=1 (audio device is not thread-safe)"
    )


@pytest.mark.usefixtures("celery_app")
def test_detection_task_is_routed_to_detection_queue(
    celery_app: Celery,
    config: Config,
):
    class Program(DetectionProgram):
        config_schema = Config

        def configure_model(self, config):
            return Mock()

    Program(config, celery_app)

    routes = celery_app.conf.task_routes or {}
    assert routes.get("detection_task") == {"queue": "detection"}, (
        "detection_task must be routed to the 'detection' queue so that "
        "apply_async() dispatches it to the concurrency=1 worker"
    )


@pytest.mark.usefixtures("celery_app")
def test_unknown_callback_queue_raises_at_setup(
    celery_app: Celery,
    config: Config,
):
    """Passing a callback_queue not in worker_config must fail early."""

    class Program(DetectionProgram):
        config_schema = Config

        def configure_model(self, config):
            return Mock()

        def register_recording_task(self, config):
            recording_task = self.create_recording_task(config)
            self.add_task(
                function=recording_task,
                callbacks=self.get_recording_callbacks(config),
                queue="recording",
                callback_queue="nonexistent_queue",
            )

    with pytest.raises(ValueError, match="nonexistent_queue"):
        Program(config, celery_app)


def test_program_only_stores_detections_with_high_threshold(
    celery_app: Celery,
    celery_worker: TestWorkController,
    config: Config,
    recording: data.Recording,
):
    threshold = 0.6

    class Program(DetectionProgram):
        config_schema = Config

        def configure_model(self, config):
            return MockModel()

    config = config.model_copy(
        update=dict(detections=DetectionsConfiguration(threshold=threshold))
    )

    program = Program(config, celery_app)
    celery_worker.reload()

    program.store.store_recording(recording)

    assert "detection_task" in program.tasks
    program.tasks["detection_task"].delay(recording).get()

    assert isinstance(program.store, SqliteStore)

    outputs = program.store.get_model_outputs(recording_ids=[recording.id])
    assert len(outputs) == 1
    output = outputs[0]

    # Check all scores are above threshold
    assert all(
        detection.detection_score >= threshold
        for detection in output.detections
    )
    assert all(
        tag.confidence_score >= threshold
        for detection in output.detections
        for tag in detection.tags
    )

    # Check no detection/tag is missed
    assert (
        min(detection.detection_score for detection in output.detections)
        == threshold
    )
    assert (
        min(
            tag.confidence_score
            for detection in output.detections
            for tag in detection.tags
        )
        == threshold
    )
