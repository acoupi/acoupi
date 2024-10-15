"""CProfile Detection Task."""

import cProfile
import logging
import pstats
from pathlib import Path
from typing import Callable

from acoupi import data
from acoupi.tasks.detection import generate_detection_task

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def cprofile_create_detection_task(
    recording: Callable[[], data.Recording],
    cprofile_output: Path = Path("home/pi/cprofile_detection.prof"),
    **kwargs,
) -> Callable[[data.Recording], None]:
    """Run and profile the detection task.

    Parameters
    ----------
    generate_detection_task : Callable
        The function to generate the detection task.
    recording : data.Recording
        The recording to run the detection task on.
    cprofile_output : str, optional
        The output file for the cProfile statistics, by default "cprofile_detection.prof".
    """
    # Create the detection task
    detection_task = generate_detection_task(**kwargs)

    # Create the cProfile object
    profiler = cProfile.Profile()

    # Run the detection task with the profiler
    profiler.runcall(detection_task, recording())

    # Save the cProfile statistics to a file
    profiler.dump_stats(cprofile_output)

    if cprofile_output:
        profiler.dump_stats(cprofile_output)
        logger.info(f"cProfile output saved to {cprofile_output}")
    else:
        stats = pstats.Stats(profiler)
        stats.strip_dirs().sort_stats("cumulative").print_stats()

    return detection_task
