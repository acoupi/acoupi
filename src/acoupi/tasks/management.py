import logging
from typing import Callable, List, Optional

from acoupi.components import types
from acoupi import data
from acoupi.files import delete_recording, get_temp_files

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def generate_file_management_task(
    store: types.Store,
    file_manager: types.RecordingSavingManager,
    logger: logging.Logger = logger,
    file_filters: Optional[List[types.RecordingSavingFilter]] = None,
    required_models: Optional[List[str]] = None,
) -> Callable[[], None]:
    """Build a process to manage files.

    Use this function to build a process that will manage files using your
    preferred file manager and store. This function will return a function
    that can be used to start the process.

    Recordings are temporarily stored on the memory to reduce the number of
    writes to the disk. This process will move recordings from the memory to
    the disk, and remove recordings that are no longer needed.
    """

    if required_models is None:
        required_models = []

    def file_management_task() -> None:
        """Manage files."""
        temp_wav_files = get_temp_files()

        recordings_and_outputs = store.get_recordings_by_path(
            paths=temp_wav_files
        )

        for recording, model_outputs in recordings_and_outputs:
            logger.info(f"Recording: {recording.path}")
            logger.info(f"Model Outputs: {model_outputs}")

            if recording.path is None:
                logger.error(
                    "Temporary recording %s has no path",
                    recording.id,
                )
                continue
            
            if len(model_outputs) == 0:
                logger.info(f"RECORDING HAS NOT BEEN PROCESSED: {recording.path}")
                continue

            else:
                new_path = file_manager.save_recording(recording, model_outputs=model_outputs)
                logger.info(f"RECORDING HAS BEEN MOVED: {new_path}")
                store.update_recording_path(recording, new_path)

    return file_management_task
