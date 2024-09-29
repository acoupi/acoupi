from subprocess import CompletedProcess, run
from typing import List

from acoupi.system.constants import Settings

__all__ = [
    "run_celery_command",
]


def run_celery_command(
    settings: Settings, args: List[str]
) -> CompletedProcess:
    cwd = settings.home.absolute()

    app_path = settings.program_file.relative_to(settings.home)
    app = ".".join(app_path.parts).replace(".py", "")

    return run(
        ["celery", "-A", str(app), *args],
        cwd=str(cwd),
    )
