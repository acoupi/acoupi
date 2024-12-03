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
            tags=[
                data.PredictedTag(
                    tag=data.Tag(key="species", value="Myotis daubentonii"),
                    confidence_score=score / 10,
                )
                for score in range(11)
            ],
            detections=[
                data.Detection(
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
    assert all(tag.confidence_score >= threshold for tag in output.tags)
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
    assert min(tag.confidence_score for tag in output.tags) == threshold
    assert (
        min(
            tag.confidence_score
            for detection in output.detections
            for tag in detection.tags
        )
        == threshold
    )
