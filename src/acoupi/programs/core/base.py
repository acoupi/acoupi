"""Definition of what a program is."""

import datetime
import logging
from abc import ABC, abstractmethod
from functools import wraps
from typing import (
    Callable,
    Generic,
    List,
    Optional,
    Protocol,
    Type,
    TypeVar,
    Union,
)

from celery import Celery, Task, group
from celery.schedules import crontab
from celery.utils.log import get_task_logger
from pydantic import BaseModel

from acoupi import data
from acoupi.programs.core.workers import AcoupiWorker, WorkerConfig

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

C = TypeVar("C", bound=BaseModel, covariant=False, contravariant=True)

B = TypeVar("B")


class InvalidAcoupiConfiguration(ValueError):
    """Raised when a configuration is invalid."""


class ProgramProtocol(Generic[C], Protocol):
    logger: logging.Logger

    def setup(self, config: C) -> None:
        pass

    def check(self, config: C) -> None:
        pass

    def on_start(self, deployment: data.Deployment) -> None:
        pass

    def on_end(self, deployment: data.Deployment) -> None:
        pass

    def add_task(
        self,
        function: Callable[[], Optional[B]],
        callbacks: Optional[List[Callable[[Optional[B]], None]]] = None,
        schedule: Union[int, datetime.timedelta, crontab, None] = None,
        queue: Optional[str] = None,
    ) -> None:
        pass


class AcoupiProgram(ABC, ProgramProtocol[ProgramConfig]):
    """A program is a collection of tasks."""

    config: ProgramConfig

    config_schema: Type[ProgramConfig]

    worker_config: Optional[WorkerConfig] = None

    app: Celery

    logger: logging.Logger

    def __init__(
        self,
        program_config: ProgramConfig,
        app: Celery,
    ):
        """Initialize."""
        self.config = program_config
        self.app = app
        self.tasks = {}
        self.logger = get_task_logger(self.__class__.__name__)
        self.setup(program_config)

    def setup(self, config: ProgramConfig):
        """Set up the program."""
        pass

    def check(self, config: ProgramConfig) -> None:
        """Check the configurations.

        This method should raise an exception if the configurations are invalid.
        The exception should be an instance of HealthCheckError.

        User defined programs should override this method if they want to
        validate their configurations. The default implementation does nothing.

        Ideally this method should be called before a deployment is made.
        """
        self.logger.info("Checking program configuration")
        self.logger.info("Configuration: %s", config)
        self.logger.info("Configuration is valid")

    def on_start(self, deployment: data.Deployment) -> None:
        """Start a deployment.

        Called when the user starts a deployment.

        This method should be overridden by user defined programs if they want
        to do something when the program starts. The default implementation
        does nothing.
        """
        self.logger.info("Starting program")
        self.logger.info("Deployment: %s", deployment)

    def on_end(self, deployment: data.Deployment) -> None:
        """End a deployment.

        Called when the user ends a deployment.

        This method should be overridden by user defined programs if they want
        to do something when the program ends. The default implementation
        does nothing.
        """
        self.logger.info("Ending program")
        self.logger.info("Deployment: %s", deployment)

    @classmethod
    def get_config_schema(cls) -> Type[BaseModel]:
        """Get the config class."""
        return cls.config_schema

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
        callbacks: Optional[List[Callable[[Optional[B]], None]]] = None,
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
                self._add_callback(callback)

            # get the task from the list of tasks
            callback_task = self.tasks[callback.__name__]

            # add the task to the list of callback tasks
            callback_tasks.append(callback_task)

        # Add the task to the list of tasks
        task = self._add_task(function, callback_tasks)

        if queue:
            # add the task to the queue
            self.add_task_to_queue(function.__name__, queue)

        if schedule:
            # configure the app to schedule the task
            self.app.add_periodic_task(schedule, task, name=task.__name__)

    def add_task_to_queue(self, task_name: str, queue: str):
        """Add a task to a queue."""
        if queue not in self.get_queue_names():
            raise ValueError(
                f"Queue {queue} is not declared in the worker config"
            )

        if not self.app.conf.task_routes:
            # initialize the task routes
            self.app.conf.task_routes = {}

        # configure the app to route the task to the queue
        self.app.conf.task_routes[task_name] = {"queue": queue}

    def _add_task(
        self,
        function: Callable[[], Optional[B]],
        callback_tasks: Optional[List[Task]] = None,
    ) -> Task:
        # TODO: Check Celery docs for best callback practices

        # Use the function name as the task name
        name = function.__name__

        logger = self.logger.getChild(name)

        # create a decorated function that will run the task and the callbacks
        @wraps(function)
        def decorated_function():
            logger.debug("Starting task")

            result = function()

            logger.debug("Task finished")

            if result is None:
                # the task did not return anything do not run the callbacks
                return

            if not callback_tasks:
                # there are no callbacks to run
                return

            logger.debug("Queueing callbacks with result: %s", result)

            # run the callbacks as a group
            callback_group = group(task.s(result) for task in callback_tasks)
            callback_group.apply_async()

        # register the task with the app
        task = self.app.task(decorated_function, name=name)

        # add the task to the list of tasks
        self.tasks[name] = task

        return task  # type: ignore

    def _add_callback(
        self,
        function: Callable[[Optional[B]], None],
    ) -> Task:
        # Use the function name as the task name
        name = function.__name__

        logger = self.logger.getChild(name)

        # create a decorated function that will run the task and the callbacks
        @wraps(function)
        def decorated_function(result: Optional[B] = None):
            logger.debug("Starting callback with result: %s", result)

            result = function(result)

            logger.debug("Callback finished")

        # register the task with the app
        task = self.app.task(decorated_function, name=name)

        # add the task to the list of tasks
        self.tasks[name] = task

        return task  # type: ignore
