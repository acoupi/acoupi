"""CProfile Messaging Task."""

import cProfile
import logging
import pstats
from pathlib import Path
from typing import Callable, List, Optional

from acoupi.components import types
from acoupi.tasks.messaging import generate_send_messages_task

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def cprofile_create_messaging_task(
    message_store: types.MessageStore,
    messengers: Optional[List[types.Messenger]] = None,
    logger: logging.Logger = logger,
    cprofile_output: Path = Path("home/pi/cprofile_messaging.prof"),
) -> Callable[[], None]:
    """Run and profile the management task.

    Parameters
    ----------
    recording : data.Recording
        The recording to run the detection task on.
    cprofile_output : str, optional
        The output file for the cProfile statistics, by default "cprofile_detection.prof".
    """
    # Create the detection task
    messaging_task = generate_send_messages_task(
        message_store=message_store,
        messengers=messengers,
        logger=logger,
    )

    def cprofile_messaging_task() -> None:
        """Run the messaging task with the cProfile."""
        profiler = cProfile.Profile()

        # Run the detection task with the profiler
        logger.info("Running the messaging_task through the profiler.")

        profiler.enable()
        messaging_task()
        profiler.disable()

        # Save the cProfile statistics to a file
        profiler.dump_stats(cprofile_output)

        if cprofile_output:
            profiler.dump_stats(cprofile_output)
            logger.info(f"cProfile output saved to {cprofile_output}")

        else:
            stats = pstats.Stats(profiler)
            stats.strip_dirs().sort_stats("cumulative").print_stats()

    return cprofile_messaging_task
