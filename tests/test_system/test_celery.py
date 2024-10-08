import pytest
from celery import Celery
from celery.contrib.testing.worker import TestWorkController

from acoupi.programs.test import TestConfigSchema
from acoupi.system import Settings
from acoupi.system.celery import (
    get_celery_bin,
    get_celery_status,
    run_celery_command,
)
from acoupi.system.lifecycle import setup_program
from acoupi.system.programs import load_program_class


@pytest.fixture
def program(settings: Settings):
    setup_program(settings, "acoupi.programs.test", [], prompt=False)
    assert settings.program_file.exists()


def test_can_find_celery_bin():
    path = get_celery_bin()
    assert path.exists()


def test_can_run_celery_command(settings: Settings):
    response = run_celery_command(
        settings,
        ["--version"],
        with_app=False,
        capture_output=True,
        text=True,
    )
    assert response.returncode == 0


def test_celery_worker_status_is_unavailable_when_not_started(
    settings: Settings,
    program,
):
    status = get_celery_status(settings)
    assert status.state == "unavailable"


@pytest.mark.usefixtures("celery_app")
@pytest.mark.usefixtures("celery_worker")
def test_can_get_celery_worker_status_with_program(
    settings: Settings,
    celery_app: Celery,
    celery_worker: TestWorkController,
    program,
):
    config = TestConfigSchema(name="test")
    program_class = load_program_class("acoupi.programs.test")
    program = program_class(
        program_config=config,
        app=celery_app,
    )

    assert "test_task" in program.tasks

    celery_worker.reload()
    celery_worker.ensure_started()

    status = get_celery_status(settings)

    assert status.state == "available"
    assert len(status.workers) == 1
    assert status.workers[0].state == "ok"
