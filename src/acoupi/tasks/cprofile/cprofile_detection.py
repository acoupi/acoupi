"""CProfile Detection Task."""

import cProfile
import logging
import pstats
from pathlib import Path
from typing import Callable, List, Optional

from acoupi import data
from acoupi.components import types
from acoupi.tasks.detection import generate_detection_task

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def cprofile_create_detection_task(
    recording: data.Recording,
    store: types.Store,
    model: types.Model,
    message_store: types.MessageStore,
    logger: logging.Logger = logger,
    output_cleaners: Optional[List[types.ModelOutputCleaner]] = None,
    processing_filters: Optional[List[types.ProcessingFilter]] = None,
    message_factories: Optional[List[types.MessageBuilder]] = None,
    cprofile_output: Path = Path("home/pi/cprofile_detection.prof"),
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
    detection_task = generate_detection_task(
        store=store,
        model=model,
        message_store=message_store,
        logger=logger,
        output_cleaners=output_cleaners,
        processing_filters=processing_filters,
        message_factories=message_factories,
    )

    # Create the cProfile object
    profiler = cProfile.Profile()

    # Run the detection task with the profiler
    logger.info("Running the detection_task through the profiler.")
    profiler.runcall(detection_task, recording)

    # Save the cProfile statistics to a file
    profiler.dump_stats(cprofile_output)

    if cprofile_output:
        profiler.dump_stats(cprofile_output)
        logger.info(f"cProfile output saved to {cprofile_output}")
    else:
        stats = pstats.Stats(profiler)
        stats.strip_dirs().sort_stats("cumulative").print_stats()

    return detection_task
