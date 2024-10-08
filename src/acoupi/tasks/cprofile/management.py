"""CProfile Management Task."""
import cProfile
import logging
import pstats
from pathlib import Path
from typing import Callable, List, Optional

from acoupi.components import types
from acoupi.system.files import TEMP_PATH
from acoupi.tasks.management import generate_file_management_task

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def generate_cprofile_management_task(
    store: types.Store,
    file_managers: List[types.RecordingSavingManager],
    logger: logging.Logger = logger,
    file_filters: Optional[List[types.RecordingSavingFilter]] = None,
    required_models: Optional[List[str]] = None,
    cprofile_output: Optional[Path] = "home/pi/storages/cprofile_output.prof",
    tmp_path: Path = TEMP_PATH
) -> Callable[[], None]:
    """Generate a file management task."""
    management_task = generate_file_management_task(
        store=store,
        file_managers=file_managers,
        logger=logger,
        file_filters=file_filters,
        required_models=required_models,
        tmp_path=tmp_path,
    )
    def cprofile_management_task() -> None:
        """Profile the file management task."""
        profiler = cProfile.Profile()
        profiler.enable()

        management_task()

        profiler.disable()

        if cprofile_output:
            profiler.dump_stats(cprofile_output)
            logger.info(f"cProfile output saved to {cprofile_output}")

        else:
            stats = pstats.Stats(profiler)
            stats.strip_dirs().sort_stats("cumulative").print_stats()

    return cprofile_management_task
