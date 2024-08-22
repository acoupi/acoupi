"""Saving managers for the recordings and detections of acoupi.

Saving managers are used to determine where and how the recordings and
detections of an audio file should be saved. This is helpful to handle
recordings files and detections outputs, such as recording and
detections outputs can be saved into a specific format (i.e, .wav files,
.csv files) and at a specific location (i.e, rpi memory, external
hardrive, folder XX/YY).

Saving managers (SavingRecording and SavingDetection) are implemented as
classes that inherit from RecordingSavingManager and
DetectionSavingManager. The classes should implement the save_recording
and save_detections methods. The save_recording method takes the
recording object, and the recording filter output. The save_detection
methods also takes a recording object and the detection filter output.
On top of these, it takes a clean list of detection to be saved.
"""

import logging
import os
import shutil
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
    """Directory path to save recordings if audio recording contains
    detections."""

    dirpath_true: Path
    """Directory path to save recordings if audio recording contains
    detections."""

    dirpath_false: Path
    """Directory path to save recordings if audio recording contain no
    detections."""

    timeformat: str
    """Datetime format to use to name the recording file path."""

    detection_threshold: float
    """Threshold to use to determine if a recording contains confident detections."""

    saving_threshold: float
    """Threshold to use to save recordings with potential (not necessarily confident) detections."""

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
        """Initiatilise the Recording SavingManager.

        Args:
            dirpath_true: Directory path to save recordings if audio recording
                contains confident detections.
            dirpath_false: Directory path to save recordings if audio recording
                contain no confident detections.
            timeformat: Datetime format to use to name the recording file path.
            detection_threshold: Threshold to use to determine if a recording contains confident detections.
            saving_threshold: Threshold to use to determine if and where the recording will be save.
        """
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
    ) -> Optional[Path]:
        """Determine where the recording should be saved."""
        if not model_outputs:
            return self.dirpath

        for model_output in model_outputs:
            # Check if any tags or detectinos are confident
            if any(
                tag.classification_probability >= self.detection_threshold
                for tag in model_output.tags
            ):
                return self.dirpath_true

            if any(
                detection.detection_probability >= self.detection_threshold
                for detection in model_output.detections
            ):
                return self.dirpath_true

            if any(
                tag.classification_probability >= self.saving_threshold
                for tag in model_output.tags
            ):
                return self.dirpath_false

            if any(
                detection.detection_probability >= self.saving_threshold
                for detection in model_output.detections
            ):
                return self.dirpath_false

        return (
            self.dirpath
        )  # Default path if any of the above conditions are not met.

    def saving_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
    ) -> Optional[Path]:
        """Determine where the recording should be saved."""
        if recording.path is None:
            raise ValueError("Recording has no path")

        sdir = self.get_saving_recording_path(model_outputs)
        srec_filename = recording.datetime.strftime(self.timeformat)

        if sdir is None:
            raise ValueError("No directory to save recording.")

        # Move recording to the path it should be saved
        new_path = sdir / f"{srec_filename}.wav"
        shutil.move(str(recording.path), new_path)
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
        """Create a new BaseFileManager.

        Args:
            directory: Directory where the files are stored.
        """
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

        Args:
            recording: Recording to get the path for.

        Returns
        -------
            Path of the file.
        """
        raise NotImplementedError

    def saving_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
    ) -> Path:
        """Save a recording to a file.

        Args:
            recording: Recording to save.

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

        # Move the file to the new location
        self.logger.warning(f"Moving {recording.path} to {full_path}")
        shutil.move(str(recording.path), full_path)

        return full_path


class DateFileManager(BaseFileManager):
    """FileManager that uses the date to organize the recordings.

    The recordings are organized in directories of the form

    YYYY/MM/DD/

    where YYYY is the year, MM is the month and DD is the day. The files
    are named using the time of the recording and its ID. The format is

    HHMMSS_ID.wav

    All the files are stored in a single directory that is specified in
    the constructor.
    """

    def get_file_path(self, recording: types.Recording) -> Path:
        """Get the path where the file of a recording should be stored.

        Args:
            recording: Recording to get the path for.

        Returns
        -------
            Path of the file.
        """
        date = recording.datetime
        directory = (
            Path(str(date.year)) / Path(str(date.month)) / Path(str(date.day))
        )
        time = recording.datetime.strftime("%H%M%S")
        return directory / Path(f"{time}_{recording.id}.wav")


class IDFileManager(BaseFileManager):
    """FileManager that uses the ID of the recording to organize the files.

    The recordings are saved in a single directory that is specified in
    the constructor. The files are named using the ID of the recording.
    The format is

    ID.wav
    """

    def get_file_path(self, recording: types.Recording) -> Path:
        """Get the the path where the file of a recording should be stored.

        Args:
            recording: Recording to get the path for.

        Returns
        -------
            Path of the file.
        """
        return Path(f"{recording.id}.wav")
