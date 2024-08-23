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
        """
        Detect events in an audio recording.

        The detection task contains the following steps:
        1. Check if the recording should be processed by the model.
        2. Run the model on the recording.
        3. Clean the outputs of the model based on the output cleaners (e.g., remove detections not meeting a user defined threshold (ThresholdDetectionFilter).)
        4. Store the cleaned outputs of the model.
        5. Create messages to be sent using the Messenger. Only create messages if outputs of the model contains valid tags (i.e., species name and associated classification probability).
        """
        logger.info("Starting detection process on recording %s", recording)

        # Check if recording should be processed
        if not all(
            filter.should_process_recording(recording)
            for filter in processing_filters or []
        ):
            # If recording should not be processed exit process
            logger.info("Recording should not be processed, skipping.")
            return

        # Detect events in recordings
        logger.info(f"Running model on recording: {recording.path}")
        model_output = model.run(recording)

        # Clean model output
        for cleaner in output_cleaners or []:
            model_output = cleaner.clean(model_output)

        # Store detections
        logger.info("Storing model output.")
        store.store_model_output(model_output)

        # Create messages
        for message_factory in message_factories or []:
            logger.info(f"Meesage_Factory: {message_factory}")
            # Check if there are any tags in the model output
            has_valid_tags = any(
                tag
                for detection in model_output.detections
                for tag in detection.tags
            )
            logger.info(f"Valid Tags: {has_valid_tags}")
            if has_valid_tags:
                message = message_factory.build_message(model_output)
                logger.info(f"Recording {recording.path} has valid tags: {has_valid_tags}.")
                logger.info("Create Message.")
                message_store.store_message(message)
            else:
                logger.info("No valid tags found.")

    return detection_task
