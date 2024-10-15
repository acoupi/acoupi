"""CProfile Management Task."""

import cProfile
import logging
import pstats
from pathlib import Path
from typing import List, Optional

from acoupi.components import types
from acoupi.system.files import TEMP_PATH
from acoupi.tasks.management import generate_file_management_task

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def cprofile_create_management_task(
    store: types.Store,
    file_managers: List[types.RecordingSavingManager],
    logger: logging.Logger = logger,
    file_filters: Optional[List[types.RecordingSavingFilter]] = None,
    required_models: Optional[List[str]] = None,
    tmp_path: Path = TEMP_PATH,
    cprofile_output: Path = Path("home/pi/cprofile_management.prof"),
):
    """Run and profile the management task.

    Parameters
    ----------
    recording : data.Recording
        The recording to run the detection task on.
    cprofile_output : str, optional
        The output file for the cProfile statistics, by default "cprofile_detection.prof".
    """
    management_task = generate_file_management_task(
        store=store,
        file_managers=file_managers,
        logger=logger,
        file_filters=file_filters,
        required_models=required_models,
        tmp_path=tmp_path,
    )

    # Create the cProfile object
    profiler = cProfile.Profile()

    # Run the detection task with the profiler
    profiler.runcall(management_task)

    # Save the cProfile statistics to a file
    profiler.dump_stats(cprofile_output)

    if cprofile_output:
        profiler.dump_stats(cprofile_output)
        logger.info(f"cProfile output saved to {cprofile_output}")
    else:
        stats = pstats.Stats(profiler)
        stats.strip_dirs().sort_stats("cumulative").print_stats()
