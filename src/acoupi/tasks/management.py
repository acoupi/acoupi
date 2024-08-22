import logging
from pathlib import Path
from typing import Callable, List, Optional

from acoupi.components import types
from acoupi.files import TEMP_PATH, get_temp_files

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def generate_file_management_task(
    store: types.Store,
    file_manager: types.RecordingSavingManager,
    logger: logging.Logger = logger,
    file_filters: Optional[List[types.RecordingSavingFilter]] = None,
    required_models: Optional[List[str]] = None,
    temp_path: Path = TEMP_PATH,
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

    required = set(required_models)

    def file_management_task() -> None:
        """Manage files."""
        logger.info(" ----  START MANAGEMENT TASK ---- ")
        temp_wav_files = get_temp_files(path=temp_path)

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

            if required - {model.name_model for model in model_outputs}:
                logger.info(f"Check that file has been processed: {model_outputs.name_model}")
                continue

            if file_filters and not all(
                file_filter.should_save_recording(recording, model_outputs)
                for file_filter in file_filters
            ):
                logger.info(
                    f"Recording does not pass filters: {recording.path}"
                )
                #recording.path.unlink()
                continue

            else: 
                new_path = file_manager.saving_recording(
                    recording, model_outputs=model_outputs
                )
                logger.info(f"New Path to recordings: {new_path}")
                if new_path is not None:
                    store.update_recording_path(recording, new_path)
                    logger.info(f"Recording has been moved: {new_path}")
                else:
                    logger.debug("Recording has not been deleted.")

    return file_management_task
