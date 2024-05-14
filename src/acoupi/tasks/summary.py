import datetime
import logging
from typing import Callable, Optional, List, TypeVar

from acoupi import data
from acoupi.components import types

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

T = TypeVar("T", bound=types.Summariser, covariant=True)


def generate_summariser_task(
    summariser: types.Summariser,
    message_factory: types.MessageBuilder,
    store: types.Store,
    message_store: types.MessageStore,
    logger: logging.Logger = logger,
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
        summary = store.summary_predictedtags_by_datetime(
            starttime=start_time,
            endtime=end_time,
        )
        
        # Create the summary content and message
        logger.info("Building summary message.")
        summary_content = summariser.build_summary(summary)
        summary_message = message_factory.build_message(
            timeinterval=data.TimeInterval(start=start_time.time(), end=end_time.time()),
            content=summary_content,
        )
        logger.info(f"Summary Message is: {summary_message}")

        # Store Message
        message_store.store_message(summary_message)
        logger.info("Message stored %s", summary_message)

    return summary_task
