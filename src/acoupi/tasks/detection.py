import logging
from typing import Callable, List, Optional, TypeVar

from acoupi import data
from acoupi.components import types
from acoupi.files import get_temp_files, get_temp_files_paths

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

    # def detection_task() -> Optional[data.ModelOutput]:
    def detection_task(recording: data.Recording) -> None:
        """Detect events in audio."""
        logger.info("Starting detection process")

        """Get recording files to process."""
        logger.info("Getting recording files to process")
        logger.info(f"Recording from recording_task: {recording}")
        # recording_temp_files_path = get_temp_files()
        # recording_temp_files_str = [get_temp_files_paths(path) for path in recording_temp_files_path]
        # logger.info(f"Found {len(recording_temp_files_str)} recording files {recording_temp_files_str}")
        # recordings = store.get_recordings_temp_path(recording_temp_files_str)

        # Check if recording should be processed
        if not all(
            # filter.should_process_recording(recording)
            filter.should_process_recording(recording)
            for filter in processing_filters or []
        ):
            # If recording should not be processed exit process
            logger.info("Recording should not be processed, skipping")
            return

        # Detect events in recordings
        logger.info("Detecting events in recordings")
        # recording = recordings[0]
        logger.info(f" --- Processing recording file {recording}")
        logger.info(f" --- Processing recording file path {recording.path}")
        model_output = model.run(recording)
        logger.info(f" --- Model Output recording file: {model_output}")

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

        # return model_output

    return detection_task  # type: ignore
