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
from typing import Callable, List, Optional, Sequence

from acoupi.components import types
from acoupi.data import ModelOutput, Recording
from acoupi.system.files import (
    TEMP_PATH,
    delete_recording,
    get_temp_files,
    move_recording,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


RecordingManagementCondition = Callable[
    [Recording, Sequence[ModelOutput]], bool
]


class ProcessedByRequiredModels:
    """Condition that checks if all required models processed a recording."""

    def __init__(self, required_model_names: List[str]):
        self.required_model_names = set(required_model_names)

    def __call__(
        self,
        recording: Recording,
        model_outputs: Sequence[ModelOutput],
    ) -> bool:
        """Return True if all required model outputs exist."""
        missing_models = self.required_model_names - {
            model.name_model for model in model_outputs
        }
        return not missing_models


def manage_recording(
    recording: Recording,
    model_outputs: List[ModelOutput],
    store: types.Store,
    file_managers: List[types.RecordingSavingManager],
    logger: logging.Logger,
    file_filters: Optional[List[types.RecordingSavingFilter]] = None,
    management_conditions: Optional[List[RecordingManagementCondition]] = None,
):
    if management_conditions is None:
        management_conditions = []

    logger.info(f"Managing recording: {recording.path}")

    if recording.path is None:
        logger.error(
            "Temporary recording %s has no path",
            recording.id,
        )
        return

    # Is the recording ready to be managed?
    for condition in management_conditions:
        if not condition(recording, model_outputs):
            logger.info(
                "Recording %s does not meet condition %s. Skipping.",
                recording,
                condition,
            )
            return

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
        return

    # Has the file already been deleted?
    if not recording.path.exists():
        logger.error(
            "Recording %s has already been deleted",
            recording,
        )
        return

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
        delete_recording(recording)


def generate_file_management_task(
    store: types.Store,
    file_managers: List[types.RecordingSavingManager],
    logger: logging.Logger = logger,
    file_filters: Optional[List[types.RecordingSavingFilter]] = None,
    required_models: Optional[List[str]] = None,
    management_conditions: Optional[List[RecordingManagementCondition]] = None,
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
    management_conditions : Optional[List[RecordingManagementCondition]], optional
        Conditions that must return True before a recording is managed. If one
        returns False, the recording stays in temporary storage. If no
        conditions are provided, all recordings are managed.
    required_models : Optional[List[str]], optional
        Model names that must process a recording before it can be managed, by
        default None.
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
    if management_conditions is None:
        management_conditions = []

    if required_models:
        management_conditions = [
            ProcessedByRequiredModels(required_models),
            *management_conditions,
        ]

    def file_management_task() -> None:
        """Manage files."""
        logger.info("Starting file management process.")
        temp_wav_files = get_temp_files(path=tmp_path)

        recordings_and_outputs = store.get_recordings_by_path(
            paths=temp_wav_files
        )
        for recording, model_outputs in recordings_and_outputs:
            manage_recording(
                recording,
                model_outputs,
                store=store,
                file_managers=file_managers,
                logger=logger,
                file_filters=file_filters,
                management_conditions=management_conditions,
            )

    return file_management_task
