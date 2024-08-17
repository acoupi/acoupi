"""Acoupi Workers Module.

This module provides the functionality for managing and configuring
AcoupiWorkers, which are essential components of the Acoupi framework for
building smart acoustic sensors. AcoupiWorkers are responsible for executing
tasks related to acoustic sensing and analysis. Each Acoupi program relies on a
set of AcoupiWorkers, each with a unique name and configuration.

The AcoupiWorker is implemented as a Celery worker, which listens to designated
queues for task execution and coordination.

"""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

__all__ = [
    "AcoupiWorker",
    "WorkerConfig",
]


class AcoupiWorker(BaseModel):
    """AcoupiWorker Class.

    Represents an individual worker instance within the Acoupi framework. It is
    responsible for executing tasks related to acoustic sensing and analysis.
    Each worker is implemented as a Celery worker and listens to designated
    queues for task execution and coordination.
    """

    name: str
    """Name of the worker. Should be unique among different workers."""

    queues: List[str] = Field(default_factory=list)
    """Queues the worker should listen to. 

    If empty, the worker will listen to all queues."""

    concurrency: Optional[int] = None
    """Number of concurrent tasks the worker should run.

    If None, the worker will run as many tasks as possible.

    This setting should be set to 1 if the worker if at most
    one task can be run at a time. This is useful for tasks
    that are not thread safe or that require use of a resource
    that can only be used by one task at a time.
    """


class WorkerConfig(BaseModel):
    """WorkerConfig Class.

    A configuration class used to define the set of workers to be used for an
    Acoupi program. It allows you to specify the details of each worker, such
    as its name, concurrency level, and the queues it listens to.
    """

    workers: List[AcoupiWorker] = Field(default_factory=list)

    @field_validator("workers")
    def unique_worker_names(cls, workers: List[AcoupiWorker]):
        """Validate that all workers have unique names."""
        names = [worker.name for worker in workers]
        if len(set(names)) != len(names):
            raise ValueError("Worker names must be unique.")
        return workers
