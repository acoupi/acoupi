"""Functions to handle files."""

from pathlib import Path
from typing import List
from uuid import UUID

TEMP_PATH = Path("/run/shm/")


__all__ = [
    "get_temp_files",
    "get_temp_file_id",
    "delete_recording",
]


def get_temp_files(path: Path = TEMP_PATH) -> List[Path]:
    """Get the list of temporary recordings.

    Temporary recordings are stored in memory to avoid unnecessary
    writes to the SD card.
    """
    wavfiles = path.glob("*.wav")
    return list(wavfiles)


def get_temp_file_id(path: Path) -> UUID:
    """Get the temporary recording UUID from the path."""
    return UUID(path.stem)


def delete_recording(path: Path) -> None:
    """Delete the recording."""
    path.unlink()
