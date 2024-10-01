"""Functions to handle files."""

import logging
import shutil
import warnings
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from acoupi import data

TEMP_PATH = Path("/run/shm/")
DEFAULT_AUDIO_STORAGE = Path.home() / "audio"

logger = logging.getLogger(__name__)


__all__ = [
    "get_temp_dir",
    "get_temp_files",
    "get_temp_file_id",
    "get_temp_files_paths",
    "delete_recording",
    "move_recording",
]


def get_temp_dir(in_memory: bool = True) -> Path:
    """Get a temporary directory where to store recordings.

    Recordings are usually stored in a staging temporary directory
    before being moved to the final storage location. This
    function returns the path of the directory where the temporary
    recordings are stored.

    Parameters
    ----------
    in_memory : bool
        If True, the temporary files will be stored in memory.

    Notes
    -----
    It is recommended to store temporary files in memory to reduce
    the number of writes to the SD card. It can also be useful in
    scenarios where recordings should not be kept in disk for legal
    reasons.

    If `in_memory` is set to True but the system does not support
    in-memory storage, the function will return the default temporary
    and show a warning.
    """
    if in_memory:
        if TEMP_PATH.exists():
            return TEMP_PATH

        warnings.warn(
            "Cannot use in memory storage for temporary files.",
            stacklevel=1,
        )

    in_tmp = Path("/tmp") / "acoupi"

    if in_tmp.parent.exists():
        return in_tmp

    return Path.home() / "tmp"


def get_temp_files(path: Path = TEMP_PATH) -> List[Path]:
    """Get the list of temporary recordings.

    Temporary recordings are stored in memory to avoid unnecessary
    writes to the SD card.
    """
    wavfiles = path.glob("*.wav")
    return list(wavfiles)


def get_temp_files_paths(path: Path) -> str:
    """Get the temporary recording path."""
    return str(path)


def get_temp_file(path: Path) -> str:
    """Get the temporary recording UUID from the path."""
    try:
        return str(path)
    except ValueError as err:
        raise ValueError(
            f"Temporary file {path} - file id {path.stem} is not a valid UUID"
        ) from err


def get_temp_file_id(path: Path) -> UUID:
    """Get the temporary recording UUID from the path."""
    try:
        return UUID(path.stem)
    except ValueError as err:
        raise ValueError(
            f"Temporary file {path} - file id {path.stem} is not a valid UUID"
        ) from err


def move_recording(
    recording: data.Recording,
    dest: Path,
    logger: Optional[logging.Logger] = None,
) -> Optional[Path]:
    """Move the recording to the destination."""
    if logger is None:
        logger = logging.getLogger(__name__)

    if recording.path is None:
        logger.error(f"Recording {recording} has no path. Couldn't be moved.")
        return

    if not dest.parent.exists():
        logger.info(f"Creating directory {dest.parent}")
        dest.parent.mkdir(parents=True)

    shutil.move(str(recording.path), str(dest))
    logging.info(f"Recording {recording} moved to {dest}")
    return dest


def delete_recording(recording: data.Recording) -> None:
    """Delete the recording."""
    if recording.path is None:
        logging.error(
            f"Recording {recording} has no path. Couldn't be deleted."
        )
        return

    recording.path.unlink()
    logging.debug(f"Recording {recording} deleted")
