"""Detection Task.

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
    """Generate a detection task.

    Parameters
    ----------
    store : types.Store
        The store to store the model output.
    model : types.Model
        The model to run on the recording.
    message_store : types.MessageStore
        The message store to store the messages.
    logger : logging.Logger, optional
        The logger to log messages, by default logger.
    output_cleaners : Optional[List[types.ModelOutputCleaner]], optional
        The output cleaners to clean the model output, by default None.
    processing_filters : Optional[List[types.ProcessingFilter]], optional
        The processing filters to check if the recording should be processed, by default None.
    message_factories : Optional[List[types.MessageBuilder]], optional
        The message factories to create messages, by default None.

    Note
    -----
    The detection task calls the following methods:

    1. **filter.should_process_recording(recording)** -> bool
        - Check if the recording should be processed by the model.
        - See [components.processing_filters][acoupi.components.processing_filters] for implementations of [types.ProcessingFilter][acoupi.components.types.ProcessingFilter].
    2. **model.run(recording)** -> data.ModelOutput
        - Run the model on the recording and return the output.
        - See [components.model_template][acoupi.components.model_template] for implementation of [types.Model][acoupi.components.types.Model].
    3. **cleaner.clean(model_output)** -> data.ModelOutput
        - Clean the outputs of the model based on the output cleaners.
        - See [components.output_cleaners][acoupi.components.output_cleaners] for implementations of [types.ModelOutputCleaner][acoupi.components.types.ModelOutputCleaner].
    4. **store.store_model_output(model_output)** -> None
        - Store the cleaned outputs of the model in the store.
        - See [components.stores][acoupi.components.stores] for implementation of [types.Store][acoupi.components.types.Store].
    5. **message_factory.build_message(model_output)** -> data.Message
        - Create messages to be sent using the Messenger.
        - See [components.message_factories][acoupi.components.message_factories] for implementations of [types.MessageBuilder][acoupi.components.types.MessageBuilder].
    6. **message_store.store_message(message)** -> None
        - Store the message in the message store.
        - See [components.message_stores][acoupi.components.message_stores] for implementation of [types.Store][acoupi.components.types.Store].
    """

    def detection_task(recording: data.Recording) -> None:
        """Run the detection process on a recording."""
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
