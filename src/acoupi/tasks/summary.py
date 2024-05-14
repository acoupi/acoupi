import datetime
import logging
from typing import Callable, TypeVar

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

        # Get Summary
        logger.info(" -- STORE GET SUMMARY -- ")
        summary = store.summary_predictedtags_by_datetime(
            starttime=start_time,
            endtime=end_time,
        )

        # Create the summary content and message
        logger.info("-- BUILDING SUMMARY MESSAGE --")

        timeinterval = dict(start=start_time.isoformat(), end=end_time.isoformat())
        summary_content = summariser.build_summary(summary)

        logger.info(f"TIMEINTERVAL: {timeinterval, type(interval)}")
        logger.info(f"SUMMARY CONTENT: {summary_content, type(summary_content)}")

        summary_message = message_factory.build_message(
            timeinterval=timeinterval,
            summary_content=summary_content,
        )

        # Store Message
        message_store.store_message(summary_message)
        logger.info("Message stored %s", summary_message)

    return summary_task
