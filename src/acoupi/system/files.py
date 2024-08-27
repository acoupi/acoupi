"""Functions to handle files."""

import logging
import shutil
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from acoupi import data

TEMP_PATH = Path("/run/shm/")
DEFAULT_AUDIO_STORAGE = Path.home() / "audio"

logger = logging.getLogger(__name__)


__all__ = [
    "get_temp_files",
    "get_temp_file_id",
    "get_temp_files_paths",
    "delete_recording",
    "move_recording",
]


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


def move_recording(recording: data.Recording, dest: Path) -> Optional[Path]:
    """Move the recording to the destination."""
    if recording.path is None:
        logging.error(f"Recording {recording} has no path. Couldn't be moved.")
        return

    if not dest.parent.exists():
        logging.debug(f"Creating directory {dest.parent}")
        dest.parent.mkdir(parents=True)

    shutil.move(str(recording.path), str(dest))
    logging.debug(f"Recording {recording} moved to {dest}")
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
