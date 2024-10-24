import json
import os
import shutil
import sys
from enum import Enum
from pathlib import Path
from subprocess import CompletedProcess, run
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from acoupi.programs.core.workers import WorkerConfig
from acoupi.system.constants import Settings
from acoupi.system.programs import load_worker_config

__all__ = [
    "run_celery_command",
    "get_celery_bin",
    "get_celery_status",
    "CeleryState",
    "WorkerState",
    "WorkerStatus",
    "CeleryStatus",
    "start_workers",
    "restart_workers",
    "stop_workers",
]


class CeleryState(str, Enum):
    UNAVAILABLE = "unavailable"
    AVAILABLE = "available"
    ERROR = "error"


class WorkerState(str, Enum):
    OK = "ok"
    NOTOK = "notok"


class WorkerStatus(BaseModel):
    worker_name: str
    state: WorkerState


class CeleryStatus(BaseModel):
    state: CeleryState

    workers: List[WorkerStatus] = Field(default_factory=list)


def get_celery_bin() -> Path:
    """Return the path to the celery binary."""
    path = shutil.which(
        "celery",
        path=f"{os.environ.get('PATH', None)}:{sys.prefix}/bin",
    )
    if path is None:
        raise RuntimeError("Could not find celery binary.")
    return Path(path)


def run_celery_command(
    settings: Settings,
    args: List[str],
    with_app: bool = True,
    quiet: bool = False,
    **kwargs,
) -> CompletedProcess:
    cwd = settings.home.absolute()

    app_path = settings.program_file.relative_to(settings.home)
    app = ".".join(app_path.parts).replace(".py", "")

    celery_bin = get_celery_bin()

    cmd = [str(celery_bin)]

    if with_app:
        cmd.extend(["-A", app])

    if quiet:
        cmd.append("-q")

    if args:
        cmd.extend(args)

    return run(cmd, cwd=str(cwd), **kwargs)


def get_celery_status(settings: Settings) -> CeleryStatus:
    response = run_celery_command(
        settings,
        ["status", "--json"],
        capture_output=True,
        text=True,
        quiet=True,
    )

    if response.returncode == 69:
        return CeleryStatus(state=CeleryState.UNAVAILABLE)

    if response.returncode != 0:
        return CeleryStatus(state=CeleryState.ERROR)

    output = response.stdout.strip().split("\n")[0]
    status = json.loads(output)
    return CeleryStatus(
        state=CeleryState.AVAILABLE,
        workers=[
            WorkerStatus(worker_name=worker_name, state=WorkerState.OK)
            for worker_name, _ in status.items()
        ],
    )


def start_workers(
    settings: Settings,
    pool: Literal[
        "threads", "prefork", "eventlet", "gevent", "solo", "processes"
    ] = "threads",
    log_level: Optional[
        Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    ] = None,
):
    """Start the Celery workers.

    Parameters
    ----------
    settings : Settings
        The current acoupi settings.
    pool : Literal, optional
        The pool type for the workers, by default "threads".
    log_level : Optional[Literal], optional
        The log level for the workers, by default None.

    Returns
    -------
    CompletedProcess
        The result of the subprocess.run function.
    """
    worker_config = load_worker_config(settings)
    return run_celery_command(
        settings,
        args=[
            "multi",
            "start",
            *_get_worker_options(worker_config),
            f"--pool={pool}",
            f"--loglevel={log_level or settings.log_level}",
            f"--pidfile={settings.run_dir}/%n.pid",
            f"--logfile={settings.log_dir}/%n%I.log",
        ],
    )


def restart_workers(
    settings: Settings,
    log_level: Optional[
        Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    ] = None,
):
    """Restart the Celery workers.

    Parameters
    ----------
    settings : Settings
        The current acoupi settings.
    log_level : Optional[Literal], optional
        The log level for the workers, by default None.

    Returns
    -------
    CompletedProcess
        The result of the subprocess.run function.
    """
    worker_config = load_worker_config(settings)
    return run_celery_command(
        settings,
        args=[
            "multi",
            "restart",
            *_get_worker_options(worker_config),
            f"--loglevel={log_level or settings.log_level}",
            f"--pidfile={settings.run_dir}/%n.pid",
            f"--logfile={settings.log_dir}/%n%I.log",
        ],
    )


def stop_workers(
    settings: Settings,
    log_level: Optional[
        Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    ] = None,
):
    """Stop the Celery workers.

    Parameters
    ----------
    settings : Settings
        The current acoupi settings.
    log_level : Optional[Literal], optional
        The log level for the workers, by default None.

    Returns
    -------
    CompletedProcess
        The result of the subprocess.run function.
    """
    worker_config = load_worker_config(settings)
    return run_celery_command(
        settings,
        args=[
            "multi",
            "stopwait",
            *[worker.name for worker in worker_config.workers],
            f"--loglevel={log_level or settings.log_level}",
            f"--pidfile={settings.run_dir}/%n.pid",
            f"--logfile={settings.log_dir}/%n%I.log",
        ],
    )


def purge_queue(settings: Settings, queue_name: str) -> CompletedProcess:
    """
    Purge all messages from the specified queue.

    Parameters
    ----------
    settings : Settings
        The settings object containing configuration for Celery.
    queue_name : str
        The name of the queue to purge.

    Returns
    -------
    CompletedProcess
        The result of the command execution.
    """
    return run_celery_command(
        settings,
        args=[
            "amqp",
            "queue.purge",
            queue_name,
        ],
        capture_output=True,
    )


def purge_queues(settings: Settings):
    """Purge all messages from all queues.

    Parameters
    ----------
    settings : Settings
        The settings object containing configuration for Celery.

    Returns
    -------
    CompletedProcess
        The result of the command execution.
    """
    worker_config = load_worker_config(settings)
    queues = {
        queue for worker in worker_config.workers for queue in worker.queues
    }
    for queue in queues:
        purge_queue(settings, queue)


def _get_worker_options(worker_config: WorkerConfig) -> list[str]:
    worker_options = []
    for worker in worker_config.workers:
        worker_options.append(worker.name)

        if worker.queues:
            worker_options.extend(
                [
                    f"-Q:{worker.name}",
                    ",".join(worker.queues),
                ]
            )

        if worker.concurrency:
            worker_options.extend(
                [
                    f"-c:{worker.name}",
                    str(worker.concurrency),
                ]
            )
    return worker_options
