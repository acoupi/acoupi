from pathlib import Path
from unittest.mock import Mock

import pytest
from celery import Celery

from acoupi.components.audio_recorder import MicrophoneConfig
from acoupi.components.messengers import HTTPConfig, MQTTConfig
from acoupi.programs.templates import (
    MessagingConfig,
    MessagingProgramConfiguration,
    MessagingProgram,
)


class Config(MessagingProgramConfiguration):
    name: str = "Test Program"


class Program(MessagingProgram):
    config_schema = Config


def test_messaging_config_fails_if_http_and_mttq_are_not_provided():
    with pytest.raises(ValueError):
        MessagingConfig()


@pytest.mark.usefixtures("celery_app")
@pytest.mark.parametrize(
    "messaging_config",
    [
        MessagingConfig(
            http=HTTPConfig(
                base_url="http://localhost:8000",
            )
        ),
        MessagingConfig(
            mqtt=MQTTConfig(
                host="localhost",
                username="test",
            )
        ),
    ],
)
def test_basic_program_with_messaging_mixin_runs_health_checks_correctly(
    celery_app: Celery,
    messaging_config: MessagingConfig,
    tmp_path: Path,
):
    config = Config(
        microphone=MicrophoneConfig(
            device_name="default",
        ),
        messaging=messaging_config.model_copy(
            update=dict(messages_db=tmp_path / "messages.db")
        ),
    )

    program = Program(
        config,
        celery_app,
    )

    mock_messenger = Mock(program.messenger)
    mock_recorder = Mock(program.recorder)
    program.messenger = mock_messenger
    program.recorder = mock_recorder

    program.check(config)

    assert mock_messenger.check.called
    assert mock_recorder.check.called


@pytest.mark.usefixtures("celery_app")
def test_program_has_correct_tasks(
    celery_app,
    microphone_config: MicrophoneConfig,
    messaging_config: MessagingConfig,
):
    config = Config(
        microphone=microphone_config,
        messaging=messaging_config,
    )
    program = Program(
        config,
        celery_app,
    )

    assert "send_messages_task" in program.tasks
    assert "heartbeat_task" in program.tasks
