import cProfile
from pathlib import Path
from typing import List, Optional

from acoupi.programs import AcoupiProgram


def get_task_list(
    program: AcoupiProgram,
    include_celery_tasks: bool = False,
) -> List[str]:
    app = program.app

    tasks = [task_name for task_name in app.tasks.keys()]

    if not include_celery_tasks:
        tasks = [task for task in tasks if "celery" not in task]

    return tasks


def run_task(
    program: AcoupiProgram,
    task_name: str,
) -> None:
    app = program.app
    if task_name not in app.tasks:
        raise ValueError(f"Task {task_name} not found.")
    task = app.tasks[task_name]
    task()


def profile_task(
    program: AcoupiProgram,
    task_name: str,
    output: Optional[Path] = None,
) -> None:
    app = program.app
    if task_name not in app.tasks:
        raise ValueError(f"Task {task_name} not found.")
    task = app.tasks[task_name]

    with cProfile.Profile() as profiler:
        profiler.enable()
        task()
        profiler.disable()

        if output is not None:
            profiler.dump_stats(str(output))
        else:
            profiler.print_stats()
