"""CProfile Detection Task."""

import cProfile
import logging
import pstats
from pathlib import Path
from typing import Callable

from acoupi.tasks.management import generate_file_management_task

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def cprofile_create_management_task(
    cprofile_output: Path = Path("home/pi/cprofile_management.prof"),
    **kwargs,
) -> Callable:
    """Run and profile the management task.

    Parameters
    ----------
    recording : data.Recording
        The recording to run the detection task on.
    cprofile_output : str, optional
        The output file for the cProfile statistics, by default "cprofile_detection.prof".
    """
    # Create the detection task
    management_task = generate_file_management_task(**kwargs)

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

    return management_task
