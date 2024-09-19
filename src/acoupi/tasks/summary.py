"""Summary Task.

This module contains the function to generate summariser task.
The summary task is a function that generates a summary message
to be sent to a remote server. The summary process contains the
following steps:

1. Generate a summary message.
2. Store the summary message in the message store.
"""

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
    """Generate a summariser task.

    Parameters
    ----------
    summarisers : List[types.Summariser]
        The summarisers to generate the summary message.
    message_store : types.MessageStore
        The message store to store the summary message.
    logger : logging.Logger, optional
        The logger to log messages, by default logger.


    Notes
    -----
    The summary process calls the following methods:

    1. **summariser.build_summary(now)** -> data.Message
        - Generate a summary message.
        - See [components.summarisers][acoupi.components.summarisers] for implementations of [types.Summariser][acoupi.components.types.Summariser].
    2. **message_store.store_message(message)** -> None
        - Store the summary message in the message store.
        - See [components.stores][acoupi.components.stores] for implementation of [types.Store][acoupi.components.types.Store].
    """

    def summary_task() -> None:
        """Create a summary message."""
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
            logger.debug(f"Summary Message Stored: {summary_message}")
            logger.debug("Message stored %s", summary_message)

    return summary_task
