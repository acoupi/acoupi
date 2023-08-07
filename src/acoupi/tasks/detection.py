import logging
from typing import Callable, List, Optional, TypeVar

from acoupi import data
from acoupi.components import types

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


T = TypeVar("T", bound=types.RecordingCondition, covariant=True)


def generate_detection_task(
    store: types.Store,
    model: types.Model,
    message_store: types.MessageStore,
    logger: logging.Logger = logger,
    output_cleaners: Optional[List[types.ModelOutputCleaner]] = None,
    processing_filters: Optional[List[types.ProcessingFilter]] = None,
    message_factories: Optional[List[types.ModelOutputMessageBuilder]] = None,
) -> Callable[[data.Recording], None]:
    """Generate a detection task."""

    def detection_task(recording: data.Recording) -> None:
        """Detect events in audio."""
        logger.info("Starting detection process")

        # Check if recording should be processed
        if not all(
            filter.should_process_recording(recording)
            for filter in processing_filters or []
        ):
            # If recording should not be processed exit process
            logger.info("Recording should not be processed, skipping")
            return

        # Detect events in recordings
        logger.info("Detecting events in recordings")
        model_output = model.run(recording)

        # Clean model output
        logger.info("Cleaning model output")
        for cleaner in output_cleaners or []:
            model_output = cleaner.clean(model_output)

        # Store detections
        store.store_model_output(model_output)

        # Create messages
        for message_factory in message_factories or []:
            message = message_factory.build_message(model_output)
            message_store.store_message(message)

    return detection_task
