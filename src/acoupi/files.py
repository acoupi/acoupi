"""Functions to handle files."""

from pathlib import Path
from typing import List
from uuid import UUID

TEMP_PATH = Path("/run/shm/")


__all__ = [
    "get_temp_files",
    # "get_temp_file_id",
    "get_temp_files_paths",
    "delete_recording",
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
    except ValueError:
        ValueError(
            f"Temporary file {path} - file id {path.stem} is not a valid UUID"
        )


def delete_recording(path: Path) -> None:
    """Delete the recording."""
    path.unlink()
