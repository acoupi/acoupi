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
    summariser_conditions: Optional[List[T]] = None,
) -> Callable[[], None]:
    """Generate a summariser task."""

    def summary_task() -> None:

        # Get ModelOutputs
        model_outputs = store.get_model_outputs_by_datetime()

        # Summarise Detections
        logger.info("Summarising model outputs")
        message = summariser.build_summary(model_outputs)

        # Store Message
        message_store.store_message(message)
        logger.info("Message stored %s", message)

    return summary_task
