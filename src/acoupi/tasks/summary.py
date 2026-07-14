"""Summary Task.

This module contains the function to generate summariser task.
The summary task is a function that generates a summary message
to be sent to a remote server. The summary process contains the
following steps:

1. Generate a summary message.
2. Store the summary message in the message store.
"""

import logging
from typing import Callable, List

from acoupi.components import types
from acoupi.data import utc_now

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

    1. **summariser.build_summary(now)** -> data.Message | list[data.Message]
        - Generate one or more summary messages.
        - See [components.summarisers][acoupi.components.summariser] for
        implementations of
        [types.Summariser][acoupi.components.types.Summariser].
    2. **message_store.store_message(message)** -> None
        - Store the summary message in the message store.
        - See [components.stores][acoupi.components.stores] for implementation
        of [types.Store][acoupi.components.types.Store].

    If a summariser returns ``None`` from ``build_summary``, the task treats
    that as "no summary available" and skips storing any message for that
    summariser. If it returns a list of messages, the task stores each one.
    """

    def summary_task() -> None:
        """Create a summary message."""
        now = utc_now()
        logger.info(
            "Starting summary generation for %d summariser(s).",
            len(summarisers),
        )

        for summariser in summarisers:
            try:
                logger.debug(
                    "Building summary message with summariser %s.",
                    summariser,
                )
                summary_messages = summariser.build_summary(now)
            except Exception as e:
                logger.error(
                    "Error building summary message for summariser %s: %s",
                    summariser,
                    e,
                )
                continue

            if summary_messages is None:
                logger.debug(
                    "Summariser %s returned no summary message. Skipping.",
                    summariser,
                )
                continue

            if not isinstance(summary_messages, list):
                summary_messages = [summary_messages]

            logger.info(
                "Storing %d summary message(s) from summariser %s.",
                len(summary_messages),
                summariser,
            )
            for summary_message in summary_messages:
                message_store.store_message(summary_message)
                logger.debug(
                    "Stored summary message from summariser %s.",
                    summariser,
                )

    return summary_task
