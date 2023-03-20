"""Definition of Recording Filters"""
from typing import List

from acoupi.types import Detection, Recording, RecordingFilter


class NegativeRecordingFilter(RecordingFilter):
    """A RecordingFilter that always returns false."""

    def should_keep_recording(
        self,
        recording: Recording,
        detections: List[Detection],
    ) -> bool:
        """Determine if a recording should be kept.

        Always returns False as no recordings should be kept.

        Args:
            recording: The recording to check.
            detections: The detections in the recording.

        Returns:
            bool
        """

        return False


class PositiveRecordingFilter(RecordingFilter):
    """A RecordingFilter that always returns true."""

    def should_keep_recording(
        self,
        recording: Recording,
        detections: List[Detection],
    ) -> bool:
        """Determine if a recording should be kept.

        Always returns True as all recordings should be kept.

        Args:
            recording: The recording to check.
            detections: The detections in the recording.

        Returns:
            bool
        """

        return True


class ThresholdRecordingFilter(RecordingFilter):
    """A RecordingFilter that keeps recordings with confident detections."""

    def __init__(self, threshold: float):
        """Initialize the filter.

        Args:
            threshold: The threshold to use.
        """

        self.threshold = threshold

    def should_keep_recording(
        self,
        recording: Recording,
        detections: List[Detection],
    ) -> bool:
        """Determine if a recording should be kept.

        Args:
            recording: The recording to check.
            detections: The detections in the recording.

        Returns:
            bool
        """

        return any(detection.probability >= self.threshold for detection in detections)


class FocusSpeciesRecordingFilter(RecordingFilter):
    """A RecordingFilter that keeps recordings with detections of species."""

    def __init__(self, species: List[str], threshold: float = 0.5):
        """Initialize the filter.

        Args:
            species: The species to focus on.
        """

        self.species = species
        self.threshold = threshold

    def should_keep_recording(
        self,
        recording: Recording,
        detections: List[Detection],
    ) -> bool:
        """Determine if a recording should be kept.

        Args:
            recording: The recording to check.
            detections: The detections in the recording.

        Returns:
            bool
        """

        return any(
            detection.probability >= self.threshold
            and detection.species_name in self.species
            for detection in detections
        )
