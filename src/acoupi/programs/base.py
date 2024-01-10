"""Definition of what a program is."""
import datetime
from abc import ABC, abstractmethod
from functools import wraps
from typing import Callable, Generic, List, Optional, Type, TypeVar, Union

from celery import Celery, group
from celery.schedules import crontab
from pydantic import BaseModel

from acoupi.programs.workers import AcoupiWorker, WorkerConfig

__all__ = [
    "NoUserPrompt",
    "AcoupiProgram",
    "ProgramConfig",
]


class NoUserPrompt:
    """No user prompt annotation.

    Use this class to annotate fields that should not be prompted to the user.
    """


ProgramConfig = TypeVar("ProgramConfig", bound=BaseModel)

B = TypeVar("B")


class InvalidAcoupiConfiguration(ValueError):
    """Raised when a configuration is invalid."""


class AcoupiProgram(ABC, Generic[ProgramConfig]):
    """A program is a collection of tasks."""

    config: Optional[ProgramConfig]

    worker_config: Optional[WorkerConfig] = None

    app: Celery

    def __init__(
        self,
        program_config: ProgramConfig,
        celery_config: BaseModel,
    ):
        """Initialize."""
        self.config = program_config
        self.app = Celery()
        self.tasks = {}

        self.app.config_from_object(celery_config)
        self.setup(program_config)

    @abstractmethod
    def setup(self, config: ProgramConfig):
        """Setup."""
        raise NotImplementedError

    def check(self, config: ProgramConfig) -> None:
        """Check the configurations.

        This method should raise an exception if the configurations are invalid.
        The exception should be an instance of HealthCheckError.

        User defined programs should override this method if they want to
        validate their configurations. The default implementation does nothing.

        Ideally this method should be called before a deployment is made.
        """
        ...

    @classmethod
    def get_config_schema(cls) -> Optional[Type[BaseModel]]:
        """Get the config class."""
        return cls.__annotations__["config"]

    @classmethod
    def get_worker_config(cls) -> WorkerConfig:
        """Get the worker config class."""
        if cls.worker_config is None:
            return WorkerConfig(workers=[AcoupiWorker(name="acoupi")])

        return cls.worker_config

    @classmethod
    def get_queue_names(cls) -> List[str]:
        """Get the queue names."""
        return [
            q
            for worker in cls.get_worker_config().workers
            for q in worker.queues
        ]

    def add_task(
        self,
        function: Callable[[], Optional[B]],
        callbacks: Optional[List[Callable[[B], None]]] = None,
        schedule: Union[int, datetime.timedelta, crontab, None] = None,
        queue: Optional[str] = None,
    ):
        """Add a task to the program."""
        if not callbacks:
            callbacks = []

        callback_tasks = []
        for callback in callbacks:
            if callback.__name__ not in self.tasks:
                # register the callback as a task with the app
                callback_task = self.app.task(callback, name=callback.__name__)
                self.tasks[callback_task.__name__] = callback_task

            # get the task from the list of tasks
            callback_task = self.tasks[callback.__name__]

            # add the task to the list of callback tasks
            callback_tasks.append(callback_task)

        # create a decorated function that will run the task and the callbacks
        @wraps(function)
        def decorated_function():
            result = function()

            if result is None:
                # the task did not return anything do not run the callbacks
                return

            if not callback_tasks:
                # there are no callbacks to run
                return

            # run the callbacks as a group
            callback_group = group(task.s(result) for task in callback_tasks)
            callback_group.apply_async()

        # register the task with the app
        task = self.app.task(decorated_function, name=function.__name__)

        # add the task to the list of tasks
        self.tasks[task.__name__] = task

        if queue:
            # make sure the queue has been declared in the worker config
            if queue not in self.get_queue_names():
                raise ValueError(
                    f"Queue {queue} is not declared in the worker config"
                )

            if not self.app.conf.task_routes:
                # initialize the task routes
                self.app.conf.task_routes = {}

            # configure the app to route the task to the queue
            self.app.conf.task_routes[task.__name__] = {"queue": queue}

        if schedule:
            # configure the app to schedule the task
            self.app.add_periodic_task(schedule, task)
