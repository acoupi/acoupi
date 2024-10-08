import json
import os
import shutil
import sys
from enum import Enum
from pathlib import Path
from subprocess import CompletedProcess, run
from typing import List

from pydantic import BaseModel, Field

from acoupi.system.constants import Settings

__all__ = [
    "run_celery_command",
    "get_celery_bin",
    "get_celery_status",
    "CeleryState",
    "WorkerState",
    "WorkerStatus",
    "CeleryStatus",
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
