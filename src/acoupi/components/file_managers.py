"""FileManagers for Acoupi.

FileManagers are used to manage the files recorded by Acoupi. 
They are used to create the file names, to create the directories,
to move the files, to delete the files, etc.

To create a new FileManager, you have to create a new class that
inherits from FileManager and implements the methods that you need.
"""
import os
import shutil
from abc import abstractmethod

from acoupi import types

__all__ = [
    "DateFileManager",
    "IDFileManager",
]


class BaseFileManager(types.FileManager):
    """Base implementation for FileManagers.

    Most of the methods of the FileManager interface are already
    implemented in this class. The only method that is not implemented
    is _get_file_path. This method must be implemented by the
    subclasses.
    """

    directory: str
    """Directory where the files are stored."""

    def __init__(self, directory: str):
        """Create a new BaseFileManager.

        Args:
            directory: Directory where the files are stored.
        """
        self.directory = directory

        if not os.path.exists(directory):
            os.makedirs(directory)

    @abstractmethod
    def _get_file_path(self, recording: types.Recording) -> str:
        """The the path where the file of a recording should be stored.

        The path must be relative to the directory specified in the
        constructor.

        Args:
            recording: Recording to get the path for.

        Returns:
            Path of the file.
        """
        raise NotImplementedError

    def save_recording(self, recording: types.Recording) -> str:
        """Save a recording to a file.

        Args:
            recording: Recording to save.

        Returns:
            Path of the saved file.
        """
        if not recording.path:
            raise ValueError("Recording has no path")

        if not os.path.exists(recording.path):
            raise FileNotFoundError("Recording file does not exist")

        # Get the path where the file should be stored
        path = self._get_file_path(recording)

        # Add the base directory as prefix
        full_path = os.path.join(self.directory, path)

        # Get the directory where the file should be stored
        directory = os.path.dirname(full_path)

        # Create the directory if it does not exist
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Move the file to the new location
        shutil.move(recording.path, full_path)

        return full_path

    def delete_recording(self, recording: types.Recording) -> None:
        """Delete a recording.

        Args:
            recording: Recording to delete.
        """
        if recording.path and os.path.exists(recording.path):
            os.remove(recording.path)


class DateFileManager(BaseFileManager):
    """FileManager that uses the date to organize the recordings.

    The recordings are organized in directories of the form

        YYYY/MM/DD/

    where YYYY is the year, MM is the month and DD is the day.
    The files are named using the time of the recording and
    its ID. The format is

        HHMMSS_ID.wav

    All the files are stored in a single directory that is
    specified in the constructor.
    """

    def _get_file_path(self, recording: types.Recording) -> str:
        """The the path where the file of a recording should be stored.

        Args:
            recording: Recording to get the path for.

        Returns:
            Path of the file.
        """
        date = recording.datetime
        directory = os.path.join(
            str(date.year),
            str(date.month),
            str(date.day),
        )
        time = recording.datetime.strftime("%H%M%S")
        return os.path.join(directory, f"{time}_{recording.id}.wav")


class IDFileManager(BaseFileManager):
    """FileManager that uses the ID of the recording to organize the files.

    The recordings are saved in a single directory that is specified
    in the constructor. The files are named using the ID of the
    recording. The format is

        ID.wav
    """

    def _get_file_path(self, recording: types.Recording) -> str:
        """The the path where the file of a recording should be stored.

        Args:
            recording: Recording to get the path for.

        Returns:
            Path of the file.
        """
        return f"{recording.id}.wav"
