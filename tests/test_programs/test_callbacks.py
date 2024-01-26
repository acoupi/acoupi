from pathlib import Path
import time

from celery import Celery
from celery.worker import WorkController
from pydantic import BaseModel

from acoupi.programs import AcoupiProgram, AcoupiWorker, WorkerConfig
from acoupi.system.configs import CeleryConfig


class Config(BaseModel):
    path: Path
    message: str


class TestProgram(AcoupiProgram):
    config: Config

    def setup(self, config: Config):
        def task_1() -> Path:
            return config.path

        def task_2(path: Path):
            path.write_text(config.message)

        self.add_task(task_1, callbacks=[task_2])


def test_does_run_callbacks(
    tmp_path: Path,
    celery_app: Celery,
    celery_worker: WorkController,
):
    path = tmp_path / "test.txt"
    message = "Hello, world!"
    config = Config(path=path, message=message)

    assert not path.exists()

    celery_config = CeleryConfig()
    program = TestProgram(
        program_config=config,
        celery_config=celery_config,
        app=celery_app,
    )
    assert celery_app.conf["accept_content"] == ["pickle"]
    celery_worker.reload()

    assert "task_1" in program.tasks
    assert "task_2" in program.tasks

    output = program.tasks["task_1"].delay()
    output.get()

    assert path.exists()
    assert path.read_text() == message


class TestProgram2(AcoupiProgram):
    config: Config

    worker_config = WorkerConfig(
        workers=[
            AcoupiWorker(
                queues=["special"],
                name="special",
                concurrency=1,
            ),
            AcoupiWorker(
                queues=["default"],
                name="default",
            ),
        ]
    )

    def setup(self, config: Config):
        def task_1() -> Path:
            return config.path

        def task_2(path: Path):
            path.write_text(config.message)

        self.add_task(task_1, callbacks=[task_2], queue="special")


def test_does_run_callbacks_in_other_queues(
    tmp_path: Path,
    celery_app: Celery,
    celery_worker: WorkController,
):
    path = tmp_path / "test.txt"
    message = "Hello, world!"
    config = Config(path=path, message=message)

    assert not path.exists()

    celery_config = CeleryConfig()
    program = TestProgram2(
        program_config=config,
        celery_config=celery_config,
        app=celery_app,
    )
    celery_worker.reload()

    assert "task_1" in program.tasks
    assert "task_2" in program.tasks

    output = program.tasks["task_1"].delay()
    output.get()

    # Need to wait a bit in case task_2 has not run yet
    time.sleep(0.1)

    assert path.exists()
    assert path.read_text() == message
