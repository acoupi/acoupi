import datetime
import logging
from typing import Callable, List

from acoupi.components import types

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def generate_summariser_task(
    summarisers: List[types.Summariser],
    message_store: types.MessageStore,
    logger: logging.Logger = logger,
) -> Callable[[], None]:
    """Generate a summariser task."""

    def summary_task() -> None:
        now = datetime.datetime.now()

        for summariser in summarisers:
            logger.info(f"SUMMARISER: {summariser}")
            try:
                summary_message = summariser.build_summary(now)
                logger.info(f"SUMMARY MESSAGE: {summary_message}")
            except Exception as e:
                logger.error(
                    "Error building summary message for summariser %s: %s",
                    summariser,
                    e,
                )
                continue

            # Store Message
            message_store.store_message(summary_message)
            logger.info(f"Summary Message Stored: {summary_message}")
            logger.debug("Message stored %s", summary_message)

    return summary_task
