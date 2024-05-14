import logging
from typing import Callable, List, Optional

from acoupi import data
from acoupi.components import types

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def generate_detection_task(
    store: types.Store,
    model: types.Model,
    message_store: types.MessageStore,
    logger: logging.Logger = logger,
    output_cleaners: Optional[List[types.ModelOutputCleaner]] = None,
    processing_filters: Optional[List[types.ProcessingFilter]] = None,
    message_factories: Optional[List[types.MessageBuilder]] = None,
) -> Callable[[data.Recording], None]:
    """Generate a detection task."""

    def detection_task(recording: data.Recording) -> None:
        """Detect events in audio."""
        logger.info("Starting detection process on recording %s", recording)

        # Check if recording should be processed
        if not all(
            filter.should_process_recording(recording)
            for filter in processing_filters or []
        ):
            # If recording should not be processed exit process
            logger.info("Recording should not be processed, skipping")
            return

        # Detect events in recordings
        logger.info("Running model on recording")
        model_output = model.run(recording)

        # Clean model output
        for cleaner in output_cleaners or []:
            model_output = cleaner.clean(model_output)
            logger.info("Cleaned model output %s", model_output)

        # Store detections
        logger.info("Storing model output")
        store.store_model_output(model_output)

        # Create messages
        for message_factory in message_factories or []:
            message = message_factory.build_message(model_output)
            logger.info("Storing message %s", message)
            message_store.store_message(message)

    return detection_task
