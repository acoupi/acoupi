from unittest.mock import Mock

import pytest
from celery import Celery

from acoupi.components.audio_recorder import MicrophoneConfig
from acoupi.programs.templates import (
    AudioConfiguration,
    DataConfiguration,
    DetectionProgramConfiguration,
    DetectionProgram,
    MessagingConfig,
)


class Config(DetectionProgramConfiguration):
    name: str = "Test Program"


@pytest.fixture
def config(
    audio_config: AudioConfiguration,
    data_config: DataConfiguration,
    microphone_config: MicrophoneConfig,
    messaging_config: MessagingConfig,
) -> Config:
    return Config(
        name="test",
        data=data_config,
        microphone=microphone_config,
        messaging=messaging_config,
        audio=audio_config,
    )


@pytest.mark.usefixtures("celery_app")
def test_can_initialize_program(
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
