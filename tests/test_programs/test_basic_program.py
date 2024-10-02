import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest
from celery import Celery

from acoupi import data
from acoupi.components.audio_recorder import MicrophoneConfig
from acoupi.programs import AcoupiProgram
from acoupi.programs.templates import (
    BasicConfiguration,
    BasicProgramMixin,
    PathsConfiguration,
)


class Program(BasicProgramMixin, AcoupiProgram):
    config: BasicConfiguration


@pytest.fixture
def config(tmp_path: Path) -> BasicConfiguration:
    return BasicConfiguration(
        paths=PathsConfiguration(
            tmp_audio=tmp_path / "tmp",
            recordings=tmp_path / "audio",
            db_metadata=tmp_path / "metadata.db",
        ),
        microphone=MicrophoneConfig(
            samplerate=44100,
            audio_channels=1,
            device_name="default",
        ),
    )


@pytest.mark.usefixtures("celery_app")
def test_basic_program_has_correct_tasks(
    celery_app: Celery,
    config: BasicConfiguration,
):
    program = Program(config, celery_app)
    assert "recording_task" in program.tasks
    assert "file_management_task" in program.tasks


@pytest.mark.usefixtures("celery_app")
def test_basic_program_registers_deployment_in_store_on_start(
    celery_app: Celery,
    config: BasicConfiguration,
):
    program = Program(config, celery_app)
    deployment = data.Deployment(
        name="test",
        latitude=12,
        longitude=32,
    )
    program.on_start(deployment)
    current = program.store.get_current_deployment()
    assert current.ended_on is None
    assert current == deployment


@pytest.mark.usefixtures("celery_app")
def test_basic_program_registers_deployment_in_store_on_end(
    celery_app: Celery,
    config: BasicConfiguration,
):
    program = Program(config, celery_app)
    deployment = data.Deployment(
        name="test",
        latitude=12,
        longitude=32,
        started_on=datetime.datetime(year=2024, month=7, day=1),
    )
    program.on_start(deployment)

    deployment.ended_on = datetime.datetime(year=2024, month=8, day=10)
    program.on_end(deployment)

    current = program.store.get_current_deployment()
    assert current.ended_on is not None


@pytest.mark.usefixtures("celery_app")
def test_basic_program_calls_recorder_check_on_check(
    celery_app: Celery,
    config: BasicConfiguration,
):
    program = Program(config, celery_app)
    program.recorder = Mock(program.recorder)
    program.check(config)
    assert program.recorder.check.called
