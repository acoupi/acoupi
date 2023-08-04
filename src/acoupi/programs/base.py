"""Definition of what a program is."""
import datetime
from abc import ABC, abstractmethod
from functools import wraps
from typing import Callable, Generic, Optional, Type, TypeVar, Union

from celery import Celery, group
from celery.schedules import crontab

from acoupi.config_schemas import BaseConfigSchema

B = TypeVar("B")
A = TypeVar("A", bound=BaseConfigSchema)


class InvalidAcoupiConfiguration(ValueError):
    """Raised when a configuration is invalid."""


class AcoupiProgram(Generic[A], ABC):
    """A program is a collection of tasks."""

    config: A

    app: Celery

    def __init__(self, config: A):
        """Initialize."""
        self.config = config
        self.app = Celery()
        self.tasks = {}

        self.app.config_from_object(config.celery)
        self.setup(config)

    @abstractmethod
    def setup(self, config: A):
        """Setup."""
        raise NotImplementedError

    def test(self, config: A) -> None:
        """Test the configurations.

        This method should raise an exception if the configurations are invalid.
        The exception should be an instance of InvalidAcoupiConfiguration.

        User defined programs should override this method if they want to
        validate their configurations. The default implementation does nothing.

        Ideally this method should be called before a deployment is made.
        """
        pass

    @classmethod
    def get_config_schema(cls) -> Type[A]:
        """Get the config class."""
        return cls.__annotations__["config"]

    def add_task(
        self,
        function: Callable[[], Optional[B]],
        callbacks: Optional[list[Callable[[B], None]]] = None,
        schedule: Union[int, datetime.timedelta, crontab, None] = None,
    ):
        """Add a task to the program."""
        if not callbacks:
            callbacks = []

        callback_tasks = []
        for callback in callbacks:
            callback_task = self.app.task(callback, name=callback.__name__)
            callback_tasks.append(callback_task)
            self.tasks[callback_task.name] = callback_task

        @wraps(function)
        def decorated_function():
            result = function()

            if result is None:
                return

            if not callback_tasks:
                return

            callback_group = group(task.s(result) for task in callback_tasks)
            callback_group.apply_async()

        task = self.app.task(decorated_function, name=function.__name__)
        self.tasks[task.name] = task

        if schedule:
            self.app.add_periodic_task(schedule, task)
