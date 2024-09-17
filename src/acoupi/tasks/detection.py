"""Detection task module.

This module contains the function to generate a detection task.
The detection task is a function that takes a recording as input and
runs the detection process on the recording. The detection process
contains the following steps:

    1. Check if the recording should be processed by the model.
    2. Run the model on the recording.
    3. Clean the outputs of the model based on the output cleaners.
    4. Store the cleaned outputs of the model in the store.
    5. Create messages to be sent using the Messenger.
"""

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
        """Run the detection process on a recording.

        Parameters
        ----------
        recording : data.Recording
            The recording to process.

        Notes
        -----
        The detection process calls the following methods:

        filter.should_process_recording(recording) -> bool
            Check if the recording should be processed by the model.
            See acoupi.components.processing_filters for implementations of types.ProcessingFilter.
        model.run(recording) -> data.ModelOutput
            Run the model on the recording and return the output.
            See acoupi.components.model_template for implementation of types.Model.
        cleaner.clean(model_output) -> data.ModelOutput
            Clean the outputs of the model based on the output cleaners.
            See acoupi.components.output_cleaners for implementations of types.ModelOutputCleaner.
        store.store_model_output(model_output) -> None
            Store the cleaned outputs of the model in the store.
            See acoupi.components.stores.sqlite.store for implementation of types.Store.
        message_factory.build_message(model_output) -> data.Message
            Create messages to be sent using the Messenger.
            See acoupi.components.message_factories for implementations of types.MessageBuilder.
        message_store.store_message(message) -> None
            Store the message in the message store.
            See acoupi.components.message_stores.sqlite.store for implementation of types.MessageStore.
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
            message = message_factory.build_message(model_output)

            if message is not None:
                logger.info("Storing message.")
                message_store.store_message(message)

    return detection_task
