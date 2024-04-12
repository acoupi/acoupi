import logging
from typing import Callable, List, Optional

from acoupi.components import types
from acoupi import data
from acoupi.files import delete_recording, get_temp_files

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def has_model_output(outputs: List[data.ModelOutput], model_name: str) -> bool:
    for output in outputs:
        if output.name_model == model_name:
            return True
    return False


def has_outputs_from_all_models(outputs: List[data.ModelOutput], model_names: List[str]) -> bool:
    for model_name in model_names:
        if not has_model_output(outputs, model_name):
            return False

    return True


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
            logger.debug(f"Recording: {recording}")
            logger.debug(f"Model Outputs: {model_outputs}")

            if recording.path is None:
                logger.error(
                    "Temporary recording %s has no path",
                    recording.id,
                )
                continue

            if not has_outputs_from_all_models(model_outputs, required_models):
                continue

            if not all(
                filter.should_save_recording(recording, model_outputs)
                for filter in file_filters or []
            ):
                logger.info(
                    "Recording %s should not be saved, deleting",
                    recording.id,
                )
                delete_recording(recording.path)
                continue

            path = file_manager.save_recording(
                recording,
                model_outputs=model_outputs,
            )

            store.update_recording_path(recording, path)

    return file_management_task
