"""Process templates for Acoupi.

Acoupi offers a collection of process templates to assist in the creation of
recording, detecting, and data sending processes. While Acoupi includes a
variety of components to construct these processes, users may prefer to use
their own components. By utilizing the provided templates, users can ensure
that their custom processes integrate with Acoupi and adhere to standardized
building practices. The use of templates also allows for effortless
customization of processes.

The templates provided take the form of functions that return a function that
can be used to start a process. Each template takes a set of arguments that
are used to construct the process. The arguments are Acoupi components
of the appropriate type, such as a message store, messenger, model, etc.
Any object that implements the appropriate interface can be used as an
argument. This allows users to use out-of-the-box components or components
that they have created themselves.
"""
import datetime
import logging
from typing import Callable, List, Optional, TypeVar

from acoupi import data
from acoupi.components import types
from acoupi.files import delete_recording, get_temp_file_id, get_temp_files

logger = logging.getLogger(__name__)


T = TypeVar("T", bound=types.RecordingCondition, covariant=True)


def generate_recording_task(
    recorder: types.AudioRecorder,
    store: types.Store,
    logger: logging.Logger = logger,
    recording_conditions: Optional[List[T]] = None,
) -> Callable[[], Optional[data.Recording]]:
    """Generate a recording task."""

    def recording_task() -> Optional[data.Recording]:
        """Record audio."""
        now = datetime.datetime.now()
        logger.info("Starting recording process")

        # Check if recording conditions are met
        if not all(
            condition.should_record(now)
            for condition in recording_conditions or []
        ):
            # If conditions not met exit process
            logger.info("Recording conditions not met.")
            return

        # Get current deployment
        deployment = store.get_current_deployment()

        # Record audio
        logger.info("Recording audio")
        recording = recorder.record(deployment)

        # Store recording metadata
        store.store_recording(recording)
        logger.info("Recording metadata stored")

        return recording

    return recording_task


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


S = TypeVar("S", bound=types.RecordingSavingFilter, covariant=True)

def generate_file_management_task(
    store: types.Store,
    file_manager: types.RecordingSavingManager,
    file_filters: Optional[List[S]] = None,
) -> Callable[[], None]:
    """Build a process to manage files.

    Use this function to build a process that will manage files using your
    preferred file manager and store. This function will return a function
    that can be used to start the process.

    Recordings are temporarily stored on the memory to reduce the number of
    writes to the disk. This process will move recordings from the memory to
    the disk, and remove recordings that are no longer needed.
    """

    def file_management_task() -> None:
        """Manage files."""
        logger.info("Starting file management process")

        temp_wav_files = get_temp_files()
        ids = [get_temp_file_id(path) for path in temp_wav_files]
        recordings_and_outputs = store.get_recordings(ids=ids)

        for recording, model_outputs in recordings_and_outputs:
            if recording.path is None:
                logger.error("Temporary recording has no path")
                continue

            if not all(
                filter.should_save_recording(recording, model_outputs)
                for filter in file_filters or []
            ):
                logger.info("Recording should not be saved, deleting")
                delete_recording(recording.path)
                continue

            path = file_manager.save_recording(
                recording,
                model_outputs=model_outputs,
            )

            store.update_recording_path(recording, path)

    return file_management_task


def generate_send_data_task(
    message_store: types.MessageStore,
    messenger: types.Messenger,
) -> Callable[[], None]:
    """Build a process to send data to a remote server.

    Use this function to build a process that will send data to a remote server
    using your preferred messenger and message store. This function will return
    a function that can be used to start the process.

    The built process will send unsynced deployments, recordings, and detections
    to the remote server. The process will then store the response from the
    remote server, so that the data can be marked as synced.

    Args:
        message_store: The message store to use. The message store
            is used to get unsynced data and store any messages that are sent.
        messenger: The messenger to use.

    Returns:
        A function that can be used to start the process.
    """

    def send_data_task() -> None:
        """Process to sync data."""
        for message in message_store.get_unsent_messages():
            response = messenger.send_message(message)
            message_store.store_response(response)

    return send_data_task
