import datetime
import logging
from typing import Callable, Optional, List, TypeVar

from acoupi.components import types

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

T = TypeVar("T", bound=types.Summariser, covariant=True)


def generate_summariser_task(
    summariser: types.Summariser,
    store: types.Store,
    message_store: types.MessageStore,
    logger: logging.Logger = logger,
    # summariser_conditions: Optional[List[T]] = None,
) -> Callable[[], None]:
    """Generate a summariser task."""

    def summary_task() -> None:

        end_time = datetime.datetime.now()
        start_time = end_time - datetime.timedelta(
            seconds=summariser.interval
        )
        logger.info(f"SUMMARY INTERVAL START: {start_time} and END: {end_time}")

        # Get Summary 
        logger.info(" -- STORE GET SUMMARY -- ")
        summary = store.summarise_predictedtags(
            starttime=start_time,
            endtime=end_time,
        )
        logger.info(f" -- SUMMARY IS: {summary}")

        # Buid and store summary message
        logger.info("Building summary message.")
        message = summariser.build_summary(summary)

        # Store Message
        message_store.store_message(message)
        logger.info("Message stored %s", message)

    return summary_task
