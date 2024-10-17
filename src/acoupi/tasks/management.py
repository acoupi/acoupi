"""Management Task for recordings.

This module contains the function to manage audio recordings. The file
management task is a function that moves recordings from temporary storage
to permanent storage and deletes recordings that are no longer needed. The
file management process contains the following steps:

1. Get the recordings that need to be managed.
2. Check if the recordings should be saved.
3. Move the recordings that should be saved outside of the temporary file system
to a permanent storage location (e.g., the sd card storage, an external hard drive).
4. Update the store with the new paths of the recordings.
"""

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


def generate_file_management_task(
    store: types.Store,
    file_managers: List[types.RecordingSavingManager],
    logger: logging.Logger = logger,
    file_filters: Optional[List[types.RecordingSavingFilter]] = None,
    required_models: Optional[List[str]] = None,
    tmp_path: Path = TEMP_PATH,
) -> Callable[[], None]:
    """Generate a file management task.

    Parameters
    ----------
    store : types.Store
        The store to get and update recordings.
    file_managers : List[types.RecordingSavingManager]
        The file managers to save recordings.
    logger : logging.Logger, optional
        The logger to log messages, by default logger.
    file_filters : Optional[List[types.RecordingSavingFilter]], optional
        The file filters to determine if recordings should be saved, by default
        None.
    required_models : Optional[List[str]], optional
        The required models that need to be saved, by default None.
    tmp_path : Path, optional
        The path where recordings are saved temporarily, by default TEMP_PATH.

    Notes
    -----
    The file management task calls the following methods:

    1. **store.get_recordings_by_path(paths)** -> List[Tuple[data.Recording, List[data.ModelOutput]]]
        - Get the recordings that need to be managed.
        - See [components.stores][acoupi.components.stores] for implementation
        of [types.Store][acoupi.components.types.Store].
    2. **filter.should_save_recording(recording, model_outputs)** -> bool
        - Determine if the recordings should be saved.
        - See [components.saving_filters][acoupi.components.saving_filters] for
        implementations of
        [types.RecordingSavingFilter][acoupi.components.types.RecordingSavingFilter].
    3. **manager.save_recording(recording, model_outputs)** -> Path
        - Move the recordings that should be saved outside of the temporary file system
        to a permanent storage location.
        - See [components.saving_managers][acoupi.components.saving_managers]
        for implementations of
        [types.RecordingSavingManager][acoupi.components.types.RecordingSavingManager].
    4. **store.update_recording_path(recording, new_path)** -> None
        - Update the store with the new paths of the recordings.
        - See [components.stores][acoupi.components.stores] for implementation
        of [types.Store][acoupi.components.types.Store].
    """
    if required_models is None:
        required_models = []

    required = set(required_models)

    def file_management_task() -> None:
        """Manage files."""
        logger.info("Starting file management process.")
        temp_wav_files = get_temp_files(path=tmp_path)

        recordings_and_outputs = store.get_recordings_by_path(
            paths=temp_wav_files
        )
        for recording, model_outputs in recordings_and_outputs:
            logger.info(f"Managing recording: {recording.path}")

            if recording.path is None:
                logger.error(
                    "Temporary recording %s has no path",
                    recording.id,
                )
                continue

            # Is the recording ready to be managed?
            if required - {model.name_model for model in model_outputs}:
                logger.info(
                    "Recording %s is not ready to be managed. Skipping.",
                    recording,
                )
                continue

            # Which files should be saved?
            if file_filters and not any(
                file_filter.should_save_recording(
                    recording,
                    model_outputs=model_outputs,
                )
                for file_filter in file_filters
            ):
                logger.info(
                    "Recording %s does not pass filters",
                    recording,
                )
                delete_recording(recording)
                continue

            # Has the file already been deleted?
            if not recording.path.exists():
                logger.error(
                    "Recording %s has already been deleted",
                    recording,
                )
                continue

            # Where should files be stored?
            for file_manager in file_managers:
                new_path = file_manager.save_recording(
                    recording,
                    model_outputs=model_outputs,
                )

                if new_path is None:
                    continue

                new_path = move_recording(recording, new_path, logger=logger)

                if new_path is not None:
                    store.update_recording_path(recording, new_path)

                break
            else:
                logger.warning(
                    "No file manager was able to save recording %s",
                    recording,
                )

    return file_management_task
