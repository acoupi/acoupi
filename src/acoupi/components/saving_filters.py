"""Recording Saving Filters.

There are various options availble for saving recordings files.

    1. Save recordings based on a specific time interval. Both parameters
       starttime_saving_recording and endtime_saving_recording need to be configured.
    2. Save recordings for x minutes before or after dawn and dusk time. Configure parameters
       before_dawndusk_duration and/or after_dawndusk_duration.
    3. Save recordings for a specific duration (i.e., x minutes)
       and with a repetitive frequency interval (i.e,  x minutes).
       Configure both parameters saving_frequency_duration and saving_frequency_interval.

Ignore all of these settings if no recordings should be saved.
"""

import datetime
from typing import List, Optional

from astral import LocationInfo
from astral.sun import sun

from acoupi import data
from acoupi.components import types

__all__ = [
    "SaveIfInInterval",
    "FrequencySchedule",
    "After_DawnDuskTimeInterval",
    "Before_DawnDuskTimeInterval",
    "FocusSpeciesRecordingFilter",
    "ThresholdRecordingFilter",
]


class SaveIfInInterval(types.RecordingSavingFilter):
    """Save recordings during specific interval of time."""

    def __init__(self, interval: data.TimeInterval, timezone: datetime.tzinfo):
        """Initialise the Interval RecordingSavingManager.

        Args:
            interval: the interval of time where recordings will be saved.
            timezone: the timezone to use when determining if recording should be saved.
        """
        self.interval = interval
        self.timezone = timezone

    def should_save_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
    ) -> bool:
        """Determine if a recording should be saved."""
        return (
            self.interval.start
            <= recording.datetime.time()
            <= self.interval.end
        )


class FrequencySchedule(types.RecordingSavingFilter):
    """Save recordings during specific interval of time."""

    def __init__(self, duration: float, frequency: float):
        """Initiatlise the FrequencySchedule RecordingSavingManager.

        Args:
            duration: the duration (time) for which recordings will be saved.
            frequency: the interval of time between each time recordings are saved.
        """
        self.duration = duration
        self.frequency = frequency

    def should_save_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
    ) -> bool:
        """Determine if a recording should be saved."""
        time = recording.datetime
        elapsed_time = (time.minute % self.frequency) + (time.second / 60)
        return elapsed_time < self.duration


class Before_DawnDuskTimeInterval(types.RecordingSavingFilter):
    """A Before Dawn Dusk Time RecordingSavingManager."""

    def __init__(self, duration: float, timezone: datetime.tzinfo):
        """Initiatlise the Before DawnDusk RecordingSavingManager.

        Args:
            duration: the duration before dawn and dusk to save recordings.
            timezone: the timezone to use when determining dawntime.
        """
        self.duration = duration
        self.timezone = timezone

    def should_save_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
    ) -> bool:
        """Determine if a recording should be saved.

        1. Get the sun information for the specific location, datetime and timezone.
        2. Substract the duration of saving recording to the dawntime, dusktime.
        3. Check if the current time falls within the dawn time interval
            or dusktime interval.
        """
        recording_time = recording.datetime.astimezone(self.timezone)

        sun_info = sun(
            LocationInfo(str(self.timezone)).observer,
            date=recording_time,
            tzinfo=self.timezone,
        )
        dawntime = sun_info["dawn"]
        dusktime = sun_info["dusk"]

        dawntime_interval = dawntime - datetime.timedelta(
            minutes=self.duration
        )
        dusktime_interval = dusktime - datetime.timedelta(
            minutes=self.duration
        )

        return (
            dawntime_interval <= recording_time <= dawntime
            or dusktime_interval <= recording_time <= dusktime
        )


class After_DawnDuskTimeInterval(types.RecordingSavingFilter):
    """After Dawn Duwk Time RecordingSavingManager."""

    def __init__(self, duration: float, timezone: datetime.tzinfo):
        """Initiatlise the After DawnTime RecordingSavingManager.

        Args:
            duration: the duration after dawn and dusk to save recordings.
            timezone: the timezone to use when determining dawntime.
        """
        self.duration = duration
        self.timezone = timezone

    def should_save_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
    ) -> bool:
        """Determine if a recording should be saved.

        1. Get the sun information for the specific location, datetime and timezone.
        2. Add the duration of saving recording to the dawntime, dusktime.
        3. Check if the current time falls within the dawn time interval
            or dusktime interval.
        """
        recording_time = recording.datetime.astimezone(self.timezone)

        sun_info = sun(
            LocationInfo(str(self.timezone)).observer,
            date=recording_time,
            tzinfo=self.timezone,
        )
        dawntime = sun_info["dawn"]
        dusktime = sun_info["dusk"]

        dawntime_interval = dawntime + datetime.timedelta(
            minutes=self.duration
        )
        dusktime_interval = dusktime + datetime.timedelta(
            minutes=self.duration
        )

        return (
            dawntime_interval <= recording_time <= dawntime
            or dusktime_interval <= recording_time <= dusktime
        )


class ThresholdRecordingFilter(types.RecordingSavingFilter):
    """Save recording if confident.

    A RecordingFilter that return True or False if an audio recording contains
    any detections above a specified threshold. The threshold argument can be
    used to set the minimum probability threshold for a detection to be
    considered confident.

    IF True : Recording is likely to contain bat calls.
    IF False: Recording is unlikely to contain bat calls.

    The result of ThresholdRecordingFilter is used by the SavingManagers. It tells the
    SavingManager how to save detections.
    """

    def __init__(self, threshold: float):
        """Initialize the filter.

        Args:
            threshold: The probability threshold to use.
        """
        self.threshold = threshold

    def is_confident_model_output(
        self, model_output: data.ModelOutput
    ) -> bool:
        """Determine if a model output is confident.

        An output is considered confident if any of its tags or detections
        have a probability greater than or equal to the threshold.

        Args:
            model_output: The model output to check.

        Returns:
            bool
        """
        if any(tag.probability >= self.threshold for tag in model_output.tags):
            return True

        return any(
            detection.probability >= self.threshold
            for detection in model_output.detections
        )

    def should_save_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
    ) -> bool:
        """Determine if a recording should be kept.

        Args:
            recording: The recording to check.
            model_outputs: The model outputs for the recording.

        Returns:
            bool
        """
        if model_outputs is None:
            return False

        return any(
            self.is_confident_model_output(model_output)
            for model_output in model_outputs
        )


class FocusSpeciesRecordingFilter(types.RecordingSavingFilter):
    """A RecordingFilter that keeps recordings with selected tags.

    This filter will keep recordings that contain confident tag
    predictions that are in the tags list.
    """

    tags: List[data.Tag]
    """The tags to focus on."""

    threshold: float
    """The probability threshold to use."""

    def __init__(self, tags: List[data.Tag], threshold: float = 0.5):
        """Initialize the filter.

        Args:
            tags: The tags to focus on.
            threshold: The probability threshold to use. Will only
            keep recordings with detections with a probability
            greater than or equal to this threshold.
        """
        self.tags = tags
        self.threshold = threshold

    def has_confident_tag(self, model_output: data.ModelOutput) -> bool:
        """Determine if a model output has a confident tag.

        An output is considered confident if any of its tags or detections
        have a probability greater than or equal to the threshold.

        Args:
            model_output: The model output to check.

        Returns:
            bool
        """
        if any(
            tag.tag in self.tags and tag.probability >= self.threshold
            for tag in model_output.tags
        ):
            return True

        for detection in model_output.detections:
            if detection.probability < self.threshold:
                continue

            print(self.tags, detection.tags)

            for tag in detection.tags:
                if tag.tag not in self.tags:
                    continue

                if tag.probability >= self.threshold:
                    return True

        return False

    def should_save_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
    ) -> bool:
        """Determine if a recording should be kept.

        Args:
            recording: The recording to check.
            detections: The detections in the recording.

        Returns:
            bool
        """
        if model_outputs is None:
            return False

        return any(
            self.has_confident_tag(model_output)
            for model_output in model_outputs
        )
