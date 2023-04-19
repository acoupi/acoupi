"""Recording filters for filtering recordings based on detections.

Recording filters are used to determine if a recording should be kept after
processing. This is useful for example if you want to only keep recordings that
satisfy certain criteria, such as those that contain detections of a certain
species or that surpass a certain probability threshold. This can be used to
reduce the storage burden of a large number of recordings. 

Recording filters are implemented as classes that inherit from RecordingFilter.
The class should implement the should_keep_recording method, which takes a
Recording object and a list of Detections and returns a boolean indicating if
the recording should be kept.
"""
from typing import List

from acoupi_types import Detection, Recording, RecordingFilter


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
    """A RecordingFilter that keeps recordings with confident detections.

    This filter will keep recordings that contain confident detections. The
    threshold argument can be used to set the minimum probability threshold for
    a detection to be considered confident.
    """

    def __init__(self, threshold: float):
        """Initialize the filter.

        Args:
            threshold: The probability threshold to use. Will only
            keep recordings with detections with a probability
            greater than or equal to this threshold.
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
        return any(
            annotation for annotation in detections if annotation['det_prob'] >= self.threshold
        )


class FocusSpeciesRecordingFilter(RecordingFilter):
    """A RecordingFilter that keeps recordings with detections of species.

    This filter will keep recordings that contain confident detections of 
    the species provided in the species argument. The threshold argument
    can be used to set the minimum probability threshold for a detection
    to be considered confident.
    """

    def __init__(self, species: List[str], threshold: float = 0.5):
        """Initialize the filter.

        Args:
            species: The species to focus on. Should be a list of
            species names.
            threshold: The probability threshold to use. Will only
            keep recordings with detections with a probability
            greater than or equal to this threshold.
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
