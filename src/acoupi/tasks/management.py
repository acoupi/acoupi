import logging
from typing import Callable, List, Optional, TypeVar

from acoupi.components import types
from acoupi.files import delete_recording, get_temp_file_id, get_temp_files

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
