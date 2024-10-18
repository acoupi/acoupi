"""Task suite for acoupi.system.tasks module."""

from pstats import Stats

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


@pytest.mark.usefixtures("celery_app")
def test_can_run_a_task(celery_app: Celery):
    class DummyProgram(AcoupiProgram):
        config_schema = Config

        def setup(self, config):
            def dummy_task():
                # NOTE: Strangely enough this test only works if the
                # print statement is here. If the test is run
                # individually without the print statement it does pass,
                # but when run with the rest of the tests it fails.
                print("Huh?")
                return "done"

            self.add_task(dummy_task, name="test_task")

    program = DummyProgram(Config(), celery_app)

    output = system.run_task(program, "test_task")

    assert output == "done"


def test_profile_returns_the_full_profile(
    setup_program,
    settings: system.Settings,
):
    program = system.load_program(settings)
    tasks = system.get_task_list(program)
    profile = system.profile_task(program, tasks[0])
    assert isinstance(profile, Stats)
