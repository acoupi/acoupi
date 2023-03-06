from abc import ABC, abstractmethod
from typing import List


class Recording:
    path: str
    datetime: str

    # Optional
    device_id: str
    lat: float
    lon: float


class AudioRecorder(ABC):
    def record(self) -> Recording:
        """Record audio from the microphone and return the path to the file

        Could potentially store other information about the recording
        in the path, such as lat/lon, datetime, device id.
        """
        ...


class Preprocessor(ABC):
    def preprocess(self, audio_path: str) -> bool:
        """Preprocess the audio file and determine if the model should be run"""
        ...


class Detection:
    species_name: str
    probability: float


class Model(ABC):
    @abstractmethod
    def run(self, recording: Recording) -> List[Detection]:
        """Run the model on the audio file and return the result"""
        ...


class Postprocessor(ABC):
    @abstractmethod
    def should_store_detection(self, detection: Detection) -> bool:
        """Determine if the detection should be stored in the database"""
        ...


class Store(ABC):
    @abstractmethod
    def store(self, detection: Detection) -> None:
        """Store the detection in the local database"""
        ...


class RecordingDecisionMaker(ABC):
    @abstractmethod
    def should_keep_recording(
        self,
        recording: Recording,
        detections: List[Detection],
        config,
    ) -> bool:
        """Determine if the recording should be kept"""
        ...


class RecordingManager(ABC):
    @abstractmethod
    def save_recording(self, recording: Recording) -> None:
        """Save the recording to the local filesystem"""
        ...

    @abstractmethod
    def delete_recording(self, recording: Recording) -> None:
        """Delete the recording"""
        ...
