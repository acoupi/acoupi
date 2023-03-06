"""This module contains the types used by the aucupi"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Recording:
    """A Recording is a single audio file recorded from the microphone"""

    path: str
    datetime: datetime
    duration: float
    samplerate: int
    device_id: Optional[str]
    lat: Optional[float]
    lon: Optional[float]


@dataclass
class Detection:
    """A Detection is a single prediction from a model."""

    species_name: str
    probability: float


class AudioRecorder(ABC):
    """The AudioRecorder is responsible for recording audio from the
    microphone"""

    def record(self) -> Recording:
        """Record audio from the microphone and return the recording.

        The recording should be saved to a temporary file and the path
        to the file should be returned, along with the datetime, duration,
        and samplerate of the recording.

        Other metadata, such as the device_id, lat, and lon, can be
        optionally returned.
        """
        ...


class ProcessingFilter(ABC):
    """The ProcessingFilter is responsible for determining if a recording
    should be processed by the model."""

    @abstractmethod
    def should_process_recording(self, recording: Recording) -> bool:
        """Determine if the recording should be processed by the model"""
        ...


class Model(ABC):
    """The Model is responsible for running the model on the audio file
    and returning the predicted detections.

    Detections should be returned as a list of Detection objects.
    """

    @abstractmethod
    def run(self, recording: Recording) -> List[Detection]:
        """Run the model on the audio file and return the result"""
        ...


class DetectorFilter(ABC):
    """The DetectorFilter is responsible for determining if a detection
    should be saved."""

    @abstractmethod
    def should_store_detection(self, detection: Detection) -> bool:
        """Determine if the detection should be stored locally"""
        ...


class Store(ABC):
    """The Store is responsible for storing the detections locally.

    It is called after the model has run. This should decide:

    1. If the detection should be stored
    2. How the detection should be stored
    """

    @abstractmethod
    def store_detections(
        self,
        recording: Recording,
        detections: List[Detection],
    ) -> None:
        """Store the detection locally"""
        ...


class RecordingFilter(ABC):
    """The RecordingFilter is responsible for determining if a recording
    should be kept or deleted. It can use the detections, the recording
    itself, and internal state to determine if the recording should be kept.
    """

    @abstractmethod
    def should_keep_recording(
        self,
        recording: Recording,
        detections: List[Detection],
    ) -> bool:
        """Determine if the recording should be kept"""
        ...


class RecordingManager(ABC):
    """The RecordingManager is responsible for saving and deleting recordings"""

    @abstractmethod
    def save_recording(self, recording: Recording) -> None:
        """Save the recording to the local filesystem"""
        ...

    @abstractmethod
    def delete_recording(self, recording: Recording) -> None:
        """Delete the recording"""
        ...
