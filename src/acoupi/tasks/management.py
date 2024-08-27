import logging
from pathlib import Path
from typing import Callable, List, Optional

from acoupi.components import types
from acoupi.system.files import (
    TEMP_PATH,
    delete_recording,
    get_temp_files,
    move_recording,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
<<<<<<< HEAD

=======
>>>>>>> 70adae0 (resolve git rebase)

def generate_file_management_task(
    store: types.Store,
    file_managers: List[types.RecordingSavingManager],
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

    Args:
        store: The store containing recordings and their associated outputs.
        file_managers: A list of file managers responsible for saving recordings.
        logger: The logger used for logging information and errors.
        file_filters: Optional list of filters to determine whether a recording should be saved.
        required_models: Optional list of models that must be present in the outputs.
        temp_path: The path where temporary files are stored.

    Returns
    -------
        A callable that executes the file management task.
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
        logger.info(f"Recordings to manage: {recordings_and_outputs}")

        for recording, model_outputs in recordings_and_outputs:
            logger.debug(f"Recording: {recording.path}")
            logger.info(f"Model Outputs: {model_outputs}")

            if recording.path is None:
                logger.error(
                    "Temporary recording %s has no path",
                    recording.id,
                )
                continue

            # Is the recording ready to be managed?
            if (not model_outputs) or (
                required - {model.name_model for model in model_outputs}
            ):
                logger.debug(
                    "Recording %s is not ready to be managed. Skipping.",
                    recording,

                )
                continue
            
            # Which files should be saved?
            for file_filter in file_filters or []:
                if not file_filter.should_save_recording(
                    recording,
                    model_outputs=model_outputs,
                ):
                    logger.debug(
                        "Recording %s does not pass filter: %s",
                        recording,
                        file_filter,
                    )
                    delete_recording(recording)
                    break

            # Has the file already been deleted?
            if not recording.path.exists():
                continue

            # Where should files be stored?
            for file_manager in file_managers:
                new_path = file_manager.saving_recording(
                    recording,
                    model_outputs=model_outputs,
                )

                if new_path is None:
                    continue

                new_path = move_recording(recording, new_path)

                if new_path is not None:
                    store.update_recording_path(recording, new_path)

                break
            else:
                logger.warning(
                    "No file manager was able to save recording %s",
                    recording,
                )

    return file_management_task
