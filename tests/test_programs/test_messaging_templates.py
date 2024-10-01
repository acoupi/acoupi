from pathlib import Path
from unittest.mock import Mock

import pytest
from celery import Celery

from acoupi.components import MicrophoneConfig
from acoupi.components.messengers import HTTPConfig, MQTTConfig
from acoupi.programs import AcoupiProgram
from acoupi.programs.templates import (
    BasicConfiguration,
    BasicProgramMixin,
    DataConfiguration,
    MessagingConfig,
    MessagingConfigMixin,
    MessagingProgramMixin,
)


class Config(BasicConfiguration, MessagingConfigMixin):
    name: str = "Test Program"


class Program(BasicProgramMixin, MessagingProgramMixin, AcoupiProgram):
    config_schema = Config


def test_messaging_config_fails_if_http_and_mttq_are_not_provided():
    with pytest.raises(ValueError):
        MessagingConfig()


@pytest.fixture
def basic_configuration(tmp_path: Path) -> BasicConfiguration:
    if not tmp_path.exists():
        tmp_path.mkdir(parents=True)

    return BasicConfiguration(
        microphone=MicrophoneConfig(
            device_name="default",
        ),
        data=DataConfiguration(
            tmp=tmp_path / "tmp",
            audio=tmp_path / "audio",
            metadata=tmp_path / "metadata.db",
        ),
    )


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
    basic_configuration: BasicConfiguration,
):
    config = Config(
        audio=basic_configuration.audio,
        data=basic_configuration.data,
        microphone=basic_configuration.microphone,
        messaging=messaging_config,
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
    celery_app: Celery,
    basic_configuration: BasicConfiguration,
):
    config = Config(
        audio=basic_configuration.audio,
        data=basic_configuration.data,
        microphone=basic_configuration.microphone,
        messaging=MessagingConfig(
            http=HTTPConfig(
                base_url="http://localhost:8000",
            )
        ),
    )
    program = Program(
        config,
        celery_app,
    )

    assert "send_messages_task" in program.tasks
    assert "heartbeat_task" in program.tasks
