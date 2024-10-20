"""Acoupi system tasks module.

This module provides a set of functions to help manage and interact with
the tasks of the currently configured acoupi program.
"""

import cProfile
from pstats import Stats
from typing import List, Optional

from acoupi import data
from acoupi.programs import AcoupiProgram


def get_task_list(
    program: AcoupiProgram,
    include_celery_tasks: bool = False,
) -> List[str]:
    """Return a list of all the tasks registered in the current program.

    Parameters
    ----------
    program : AcoupiProgram
        The AcoupiProgram instance to get the tasks from.
    include_celery_tasks : bool, optional
        Whether to include celery tasks in the list. Defaults to False.

    Returns
    -------
    List[str]
        List of the names of available tasks.

    Notes
    -----
    Celery registers a number of tasks by default, which can be excluded
    from the list by setting `include_celery_tasks` to `False`.
    """
    app = program.app

    tasks = [task_name for task_name in app.tasks.keys()]

    if not include_celery_tasks:
        tasks = [task for task in tasks if "celery" not in task]

    return tasks


def run_task(
    program: AcoupiProgram,
    task_name: str,
    recording: Optional[data.Recording] = None,
):
    """Run a task from the current program.

    Parameters
    ----------
    program : AcoupiProgram
        The AcoupiProgram instance to run the task from.
    task_name : str
        The name of the task to run.

    Raises
    ------
    ValueError
        If the specified task is not found.

    Notes
    -----
    This function runs the task in the current Python process and does not
    send the task to the Celery workers. This can be helpful for testing a
    task without setting up Celery workers. To run the task through Celery
    workers, use the `acoupi celery call <task_name>` command.
    """
    app = program.app
    if task_name not in app.tasks:
        raise ValueError(f"Task {task_name} not found.")
    task = app.tasks[task_name]

    if task_name != "detection_task":
        return task.apply().get()

    if task_name == "detection_task" and recording is None:
        raise ValueError(
            "Can't instantiate detection_task, no recording object is given. Provide a valid data.Recording object."
        )
    if task_name == "detection_task" and recording is not None:
        return task.apply((recording,)).get()


def profile_task(
    program: AcoupiProgram,
    task_name: str,
) -> Stats:
    """Profile a task from the current program.

    Parameters
    ----------
    program : AcoupiProgram
        The AcoupiProgram instance to profile the task from.
    task_name : str
        The name of the task to profile.
    output : Optional[Path], optional
        The path to save the profiling output. If not provided,
        the output will be printed to the console. Defaults to None.

    Raises
    ------
    ValueError
        If the specified task is not found.

    Notes
    -----
    This function uses cProfile to profile the task. The output can
    be saved to a file by providing the `output` parameter. The task
    is run in the current Python process and does not send the task to
    the Celery workers, so the profiling will only show the performance
    of the task without the overhead of the Celery workers.
    """
    app = program.app
    if task_name not in app.tasks:
        raise ValueError(f"Task {task_name} not found.")
    task = app.tasks[task_name]

    with cProfile.Profile() as profiler:
        task()

        profiler.create_stats()
        return Stats(profiler)
