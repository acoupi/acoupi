"""Saving managers for the recordings and detections of acoupi.

Saving managers are used to determine where and how the recordings and
detections of an audio file should be saved. This is helpful to handle
recordings files and detections outputs. Recordings and detections outputs
can be saved into a specific format (i.e, .wav files, .csv files) and at a
specific location (i.e, rpi memory, external hardrive, folder XX/YY).

The SavingManagers are implemented as class that inherit from RecordingSavingManager.
The classes should implement the save_recording method. The save_recording method
takes a recording object and a list of model outputs as input and returns the path where
the recording should be saved.

The save_recording method is called by the file management task to determine where the
recording should be saved. The file management task is responsible for moving recordings
from the memory to the disk, and remove recordings that are no longer needed.

The SavingManagers are optional and can be ingored if the no recordings are saved.
"""

import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from celery.utils.log import get_task_logger

from acoupi import data
from acoupi.components import types

__all__ = [
    "SaveRecordingManager",
    "IDFileManager",
    "DateFileManager",
]


class SaveRecordingManager(types.RecordingSavingManager):
    """A Recording SavingManager that save audio recordings."""

    dirpath: Path
    """Directory path to save recordings."""

    dirpath_true: Path
    """Directory path to save recordings if audio recording contains confident detections
    (i.e., above the detection threshold)."""

    dirpath_false: Path
    """Directory path to save recordings if audio recording contain no confident detections
    (i.e., below the detection threshold)."""

    timeformat: str
    """Datetime format to use to name the recording file path."""

    detection_threshold: float
    """Threshold determining if a recording contains confident detections."""

    saving_threshold: float
    """Threshold determining if recordings should be saved (i.e., regardless of confident
    or unconfident detections)."""

    def __init__(
        self,
        dirpath: Path,
        dirpath_true: Optional[Path] = None,
        dirpath_false: Optional[Path] = None,
        timeformat: str = "%Y%m%d_%H%M%S",
        detection_threshold: float = 0.6,
        saving_threshold: float = 0.3,
        logger: Optional[logging.Logger] = None,
    ):
        """Initiatilise the Recording SavingManager."""
        if not dirpath.exists():
            dirpath.mkdir(parents=True)
        self.dirpath = dirpath

        if dirpath_true is None:
            dirpath_true = dirpath / "true_detections"
        if not dirpath_true.exists():
            dirpath_true.mkdir(parents=True)
        self.dirpath_true = dirpath_true

        if dirpath_false is None:
            dirpath_false = dirpath / "false_detections"
        if not dirpath_false.exists():
            dirpath_false.mkdir(parents=True)
        self.dirpath_false = dirpath_false

        self.timeformat = timeformat
        self.detection_threshold = detection_threshold
        self.saving_threshold = saving_threshold

        if logger is None:
            logger = get_task_logger(__name__)
        self.logger = logger

    def get_saving_recording_path(
        self,
        model_outputs: Optional[List[data.ModelOutput]],
    ) -> Path:
        """Determine where the recording should be saved.

        Parameters
        ----------
        model_outputs : Optional[List[data.ModelOutput]]
            List of model outputs containing detections and tags.

        Returns
        -------
        Path
            Path where the recording should be saved.
        """
        if not model_outputs:
            return self.dirpath

        for model_output in model_outputs:
            # Check if any tags or detectinos are confident
            if any(
                tag.confidence_score >= self.detection_threshold
                for tag in model_output.tags
            ):
                return self.dirpath_true

            if any(
                detection.detection_score >= self.detection_threshold
                for detection in model_output.detections
            ):
                return self.dirpath_true

            if any(
                tag.confidence_score >= self.saving_threshold
                for tag in model_output.tags
            ):
                return self.dirpath_false

            if any(
                detection.detection_score >= self.saving_threshold
                for detection in model_output.detections
            ):
                return self.dirpath_false

        return (
            self.dirpath
        )  # Default path if any of the above conditions are not met.

    def save_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
    ) -> Path:
        """Save a recording to a file.

        Examples
        --------
        >>> dirpath = Path("path/to/save")
        >>> dirpath_true = Path("path/to/save/confident_detections")
        >>> dirpath_false = Path("path/to/save/unconfident_detections")
        >>> detection_threshold = 0.8
        >>> saving_threshold = 0.3

        >>> model_outputs = [
        ...     data.ModelOutput(tags=[data.Tag(confidence_score=0.7)]),
        ...     data.ModelOutput(
        ...         detections=[data.Detection(detection_score=0.6)]
        ...     ),
        ... ]
        >>> saving_directory = self.get_saving_recording_path(
        ...     model_outputs
        ... )
        >>> assert saving_directory == dirpath_false
        """
        if recording.path is None:
            raise ValueError("Recording has no path")

        sdir = self.get_saving_recording_path(model_outputs)
        srec_filename = recording.created_on.strftime(self.timeformat)

        if sdir is None:
            raise ValueError("No directory to save recording.")

        # Move recording to the path it should be saved
        new_path = sdir / f"{srec_filename}.wav"
        return new_path


class BaseFileManager(types.RecordingSavingManager, ABC):
    """Base implementation for simple recording saving managers.

    This class can be used to implement simple recording saving managers
    that do not use model outputs to determine where the recording
    should be saved.

    All recordings are saved in a directory specified in the constructor
    and the relative path is determined by the get_file_path method.
    """

    directory: Path
    """Directory where the files are stored."""

    def __init__(
        self, directory: Path, logger: Optional[logging.Logger] = None
    ):
        """Create a new BaseFileManager."""
        if logger is None:
            logger = get_task_logger(__name__)
        self.logger = logger
        self.directory = directory

        if not os.path.exists(directory):
            os.makedirs(directory)

    @abstractmethod
    def get_file_path(self, recording: data.Recording) -> Path:
        """Get the path where the file of a recording should be stored.

        The path must be relative to the directory specified in the
        constructor.

        Parameters
        ----------
        recording: data.Recording
            Recording to get the path for.

        Returns
        -------
            Path of the file.
        """
        raise NotImplementedError

    def save_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
    ) -> Path:
        """Save a recording to a file.

        Parameters
        ----------
        recording: data.Recording
            Recording to save.

        Returns
        -------
            Path of the saved file.
        """
        if not recording.path:
            raise ValueError("Recording has no path")

        if not recording.path.is_file():
            raise FileNotFoundError("Recording file does not exist")

        # Get the path where the file should be stored
        path = self.get_file_path(recording)

        # Add the base directory as prefix
        full_path = self.directory / path

        # Get the directory where the file should be stored
        directory = full_path.parent

        # Create the directory if it does not exist
        if not os.path.exists(directory):
            os.makedirs(directory)

        return full_path


class DateFileManager(BaseFileManager):
    """FileManager that uses the date to organise the recordings.

    The recordings are organised in directories of the form

    YYYY/MM/DD/

    where YYYY is the year, MM is the month and DD is the day. The files
    are named using the time of the recording and its ID. The format is

    HHMMSS_ID.wav

    All the files are stored in a single directory that is specified in
    the constructor.
    """

    def get_file_path(self, recording: data.Recording) -> Path:
        """Get the path where the file of a recording should be stored.

        Parameters
        ----------
        recording
            Recording to get the path for.

        Returns
        -------
            Path of the file.
        """
        date = recording.created_on
        directory = (
            Path(str(date.year)) / Path(str(date.month)) / Path(str(date.day))
        )
        time = recording.created_on.strftime("%H%M%S")
        return directory / Path(f"{time}_{recording.id}.wav")


class IDFileManager(BaseFileManager):
    """FileManager that uses the ID of the recording to organise the files.

    The recordings are saved in a single directory that is specified in
    the constructor. The files are named using the ID of the recording.
    The format is

    ID.wav
    """

    def get_file_path(self, recording: data.Recording) -> Path:
        """Get the the path where the file of a recording should be stored."""
        return Path(f"{recording.id}.wav")
