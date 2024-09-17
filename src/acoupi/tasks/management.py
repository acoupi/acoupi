"""Management tasks for recordings.

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
    temp_path: Path = TEMP_PATH,
) -> Callable[[], None]:
    """Generate a file management task."""
    if required_models is None:
        required_models = []

    required = set(required_models)

    def file_management_task() -> None:
        """Manage files.

        Notes
        -----
        The file management process calls the following methods:

        store.get_recordings_by_path(paths) -> List[Tuple[data.Recording, List[data.ModelOutput]]]
            Get the recordings that need to be managed.
            See acoupi.components.stores.sqlite.store for implementation of types.Store.
        filter.should_save_recording(recording, model_outputs) -> bool
            Determine if the recordings should be saved.
            See acoupi.components.saving_filters for implementations of types.RecordingSavingFilter.
        manager.save_recording(recording, model_outputs) -> Path
            Move the recordings that should be saved outside of the temporary file system
            to a permanent storage location.
            See acoupi.components.saving_managers for implementations of types.RecordingSavingManager.
        store.update_recording_path(recording, new_path) -> None
            Update the store with the new paths of the recordings.
            See acoupi.components.stores.sqlite.store for implementation of types.Store.
        """
        logger.info("Starting file management process.")
        temp_wav_files = get_temp_files(path=temp_path)

        recordings_and_outputs = store.get_recordings_by_path(
            paths=temp_wav_files
        )
        logger.info(f"Recordings to manage: {recordings_and_outputs}")

        for recording, model_outputs in recordings_and_outputs:
            logger.info(f"Recording: {recording.path}")

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
