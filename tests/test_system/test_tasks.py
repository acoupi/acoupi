"""Task suite for acoupi.system.tasks module."""

from pstats import Stats
from unittest import mock

import pytest
from celery import Celery
from pydantic import BaseModel

from acoupi import system
from acoupi.programs import AcoupiProgram


class Config(BaseModel):
    a: int = 1


@pytest.fixture
def setup_program(settings: system.Settings):
    system.setup_program(settings, "acoupi.programs.test", prompt=False)


def test_list_of_tasks_does_not_show_default_celery_tasks(
    setup_program,
    settings: system.Settings,
):
    program = system.load_program(settings)
    tasks = system.get_task_list(program)
    assert not any("celery" in task for task in tasks)


def test_can_run_a_task():
    task = mock.Mock()

    class Program(AcoupiProgram):
        config_schema = Config

        def setup(self, config):
            self.add_task(task, name="test_task")

    program = Program(Config(), Celery())

    system.run_task(program, "test_task")

    task.assert_called()


def test_profile_returns_the_full_profile(
    setup_program,
    settings: system.Settings,
):
    program = system.load_program(settings)
    tasks = system.get_task_list(program)
    profile = system.profile_task(program, tasks[0])
    assert isinstance(profile, Stats)
