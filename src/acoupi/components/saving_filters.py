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
    "DetectionTagValue",
    "DetectionTags",
    "SavingThreshold",
]


class SaveIfInInterval(types.RecordingSavingFilter):
    """A time interval SavingFilter."""

    interval: data.TimeInterval
    """The interval of time where recordings will be saved."""

    timezone: datetime.tzinfo
    """The timezone to use when determining if recording should be saved."""

    def __init__(self, interval: data.TimeInterval, timezone: datetime.tzinfo):
        """Initialise the SaveIfInterval SavingFilter."""
        self.interval = interval
        self.timezone = timezone

    def should_save_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
    ) -> bool:
        """Determine if a recording falls within the interval.

        Examples
        --------
        >>> interval = data.TimeInterval(start=datetime.time(21, 30), end=datetime.time(23, 00))
        >>> timezone = datetime.timezone.utc
        >>> filter = SaveIfInInterval(interval, timezone)
        >>> recording = data.Recording(datetime=datetime.datetime(2024, 1, 1, 22, 0, 0, tzinfo=timezone))
        >>> filter.should_save_recording(recording)
        True
        """
        time = recording.datetime.time()
        if self.interval.start > self.interval.end:
            return self.interval.start <= time or time <= self.interval.end

        return self.interval.start <= time <= self.interval.end


class FrequencySchedule(types.RecordingSavingFilter):
    """A frequency schedule SavingFilter."""

    duration: float
    """The duration of time (in minutes) where recordings will be saved."""

    frequency: float
    """The frequency of time (in minutes) where recordings will be saved."""

    def __init__(self, duration: float, frequency: float):
        """Initialise the FrequencySchedule SavingFilter."""
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
    """A before dawn and dusk time SavingFilter."""

    def __init__(self, duration: float, timezone: datetime.tzinfo):
        """Initiatlise the Before Dawn & Dusk SavingFilter."""
        self.duration = duration
        self.timezone = timezone

    def should_save_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
    ) -> bool:
        """Determine if a recording falls within the specified interval, before dawn and dusk.

        Notes
        -----
        The dawn and dusk times are calculated using the `astral` library. The 
        `sun` function returns the dawn and dusk times for a specific location, datetime
        and timezone. This information is used to determine the interval before dawn and dusk
        dusk, and whether the current recording falls within this interval.
        DawnTime GMT: 2024-01-01 07:26:00+00:00
        DuskTime GMT: 2024-01-01 16:42:00+00:00
        >>> duration = 30
        >>> timezone = "Europe/London"
        >>> saving_filter = Before_DawnDuskTimeInterval(duration, timezone)  
        >>> recording = data.Recording(datetime=datetime.datetime(2024, 1, 1, 7, 0, 0, tzinfo=timezone))
        >>> saving_filter.should_save_recording(recording)
        True

        >>> duration = 30
        >>> timezone = "Europe/London"
        >>> saving_filter = Before_DawnDuskTimeInterval(duration, timezone)
        >>> recording = data.Recording(datetime=datetime.datetime(2024, 1, 1, 17, 0, 0, tzinfo=timezone))
        >>> saving_filter.should_save_recording(recording)
        False
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

        return (dawntime_interval <= recording_time <= dawntime) or (
            dusktime_interval <= recording_time <= dusktime
        )


class After_DawnDuskTimeInterval(types.RecordingSavingFilter):
    """An after dawn and dusk time SavingFilter."""

    duration: float
    """The duration (in minutes) before dawn and dusk where recordings will be saved."""

    timezone: datetime.tzinfo
    """The timezone to use when determining dawntime and dusktime."""

    def __init__(self, duration: float, timezone: datetime.tzinfo):
        """Initiatlise the Before Dawn & Dusk SavingFilter."""
        self.duration = duration
        self.timezone = timezone

    def should_save_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
    ) -> bool:
        """Determine if a recording falls within the specified interval, after dawn and dusk.

        Notes
        -----
        The dawn and dusk times are calculated using the `astral` library. The 
        `sun` function returns the dawn and dusk times for a specific location, datetime
        and timezone. This information is used to determine the interval after dawn and dusk
        dusk, and whether the current recording falls within this interval.

        Examples
        --------
        DawnTime GMT: 2024-01-01 07:26:00+00:00
        DuskTime GMT: 2024-01-01 16:42:00+00:00
        >>> duration = 30
        >>> timezone = "Europe/London"
        >>> saving_filter = After_DawnDuskTimeInterval(duration, timezone)  
        >>> recording = data.Recording(datetime=datetime.datetime(2024, 1, 1, 7, 0, 0, tzinfo=timezone))
        >>> saving_filter.should_save_recording(recording)
        False

        >>> duration = 30
        >>> timezone = "Europe/London"
        >>> saving_filter = After_DawnDuskTimeInterval(duration, timezone)
        >>> recording = data.Recording(datetime=datetime.datetime(2024, 1, 1, 17, 0, 0, tzinfo=timezone))
        >>> saving_filter.should_save_recording(recording)
        True
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

        return (dawntime <= recording_time <= dawntime_interval) or (
            dusktime <= recording_time <= dusktime_interval
        )


class SavingThreshold(types.RecordingSavingFilter):
    """A SavingTreshold filter."""

    saving_threshold: float
    """The probability threshold to use."""

    def __init__(self, saving_threshold: float):
        """Initialize the SavingFilter."""
        self.saving_threshold = saving_threshold

    def has_confident_model_output(
        self, model_output: data.ModelOutput
    ) -> bool:
        """Determine if a model output has confident detections or tags.

        An output is considered confident if any of its detection probability
        or classification tag probability is greater than or equal to the threshold.

        Parameters
        ----------
        model_output : data.ModelOutput
            The model output of the recording containing detections and tags.
        
        Returns
        -------
        bool
            True if any detection or classification probability is above the saving threshold.
            False if no detection or classification probability is above the saving threshold. 
        """
        if any(
            tag.classification_probability >= self.saving_threshold
            for tag in model_output.tags
        ):
            return True

        if any(
            detection.detection_probability >= self.saving_threshold
            for detection in model_output.detections
        ):
            return True

        return False

    def should_save_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
    ) -> bool:
        """Determine if a recording contains any detections or classification probabilities above the saving threshold."""
        if model_outputs is None:
            return False

        return any(
            self.has_confident_model_output(model_output)
            for model_output in model_outputs
        )


class DetectionTagValue(types.RecordingSavingFilter):
    """A RecordingFilter that keeps recordings with specific tag values."""

    values: List[str]
    """The tag values to focus on."""

    def __init__(self, values: List[str]):
        """Initialize the SavingFilter."""
        self.values = values

    def has_confident_tagvalues(self, model_output: data.ModelOutput) -> bool:
        """Determine if a model output has a confident tag values.

        An output is considered confident if any of its tag value (e.g., species_name)
        is in the values list.

        Parameters
        ----------
        model_output : data.ModelOutput
            The model output of the recording containing detections and tags.

        Returns
        -------
            bool
        """
        for detection in model_output.detections:
            for tag in detection.tags:
                if tag.tag.value in self.values:
                    return True
        return False

    def should_save_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
    ) -> bool:
        """Determine if the model output of a recording contains any confident tag values."""
        if model_outputs is None:
            return False

        return any(
            self.has_confident_tagvalues(model_output)
            for model_output in model_outputs
        )


class DetectionTags(types.RecordingSavingFilter):
    """A RecordingFilter that keeps recordings with selected tags.

    This filter will keep recordings that contain confident tag
    predictions that are in the tags list.
    """

    tags: List[data.Tag]
    """The tags to focus on."""

    saving_threshold: float
    """The probability threshold to use."""

    def __init__(self, tags: List[data.Tag], saving_threshold: float = 0.5):
        """Initialize the SavingFilter."""
        self.tags = tags
        self.saving_threshold = saving_threshold

    def has_confident_tag(self, model_output: data.ModelOutput) -> bool:
        """Determine if a model output has a confident tag.

        An output is considered confident if any of its tags or detections
        have a probability greater than or equal to the threshold.

        Parameters: 
        ----------
        model_output : data.ModelOutput
            The model output of the recording containing detections and tags.

        Returns
        -------
            bool
        """
        if any(
            tag.tag in self.tags
            and tag.classification_probability >= self.saving_threshold
            for tag in model_output.tags
        ):
            return True

        for detection in model_output.detections:
            if detection.detection_probability < self.saving_threshold:
                continue

            for tag in detection.tags:
                if tag.tag not in self.tags:
                    continue

                if tag.classification_probability >= self.saving_threshold:
                    return True

        return False

    def should_save_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
    ) -> bool:
        """Determine if the model output of a recording contains any confident tags or detection probabilities above a threshold."""
        if model_outputs is None:
            return False

        return any(
            self.has_confident_tag(model_output)
            for model_output in model_outputs
        )
