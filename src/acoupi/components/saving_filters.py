"""Recording Saving Filters for acoupi.

RecordingSavingFilters are used to determine if a recording should be saved based on
specific criteria. These filters can be used to save recordings based on time intervals,
detection probabilities, classification probabilities, classification tag values, and more.

The Recording SavingFilters are implemented as classes that inherit from the RecordingSavingFilter
Implementation of the RecordingSavingFilters should implement the should_save_recording method,
which takes a recording object and a list of model outputs, and returns a boolean value.

The RecordingSavingFilters are used in the acoupi.tasks.management module to determine
if a recording should be saved based on the output of the models and the filters provided.
If a recording pass filters, it will be kept and stored in a directory specified by the
RecordingSavingManager. If a recording does not pass the filters, it is deleted.

The RecordingSavingFilters are optional and can be ignored if no recordings should be saved.
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
    """A time interval RecordingSavingFilter."""

    interval: data.TimeInterval
    """The interval of time where recordings will be saved."""

    timezone: datetime.tzinfo
    """The timezone to use when determining if recording should be saved."""

    def __init__(self, interval: data.TimeInterval, timezone: datetime.tzinfo):
        """Initialise the SaveIfInterval RecordingSavingFilter."""
        self.interval = interval
        self.timezone = timezone

    def should_save_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
    ) -> bool:
        """Save a recording if it falls within the specified interval.

        Examples
        --------
        >>> interval = data.TimeInterval(
        ...     start=datetime.time(21, 30), end=datetime.time(23, 00)
        ... )
        >>> timezone = datetime.timezone.utc
        >>> filter = SaveIfInInterval(interval, timezone)
        >>> recording = data.Recording(
        ...     datetime=datetime.datetime(
        ...         2024, 1, 1, 22, 0, 0, tzinfo=timezone
        ...     )
        ... )
        >>> filter.should_save_recording(recording)
        True
        """
        time = recording.created_on.time()
        if self.interval.start > self.interval.end:
            return self.interval.start <= time or time <= self.interval.end

        return self.interval.start <= time <= self.interval.end


class FrequencySchedule(types.RecordingSavingFilter):
    """A frequency schedule RecordingSavingFilter."""

    duration: int
    """The duration of time (in minutes) where recordings will be saved."""

    frequency: int
    """The frequency of time (in minutes) where recordings will be saved."""

    def __init__(self, duration: int, frequency: int):
        """Initialise the FrequencySchedule RecordingSavingFilter."""
        self.duration = duration
        self.frequency = frequency

    def should_save_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
    ) -> bool:
        """Determine if a recording should be saved."""
        time = recording.created_on
        elapsed_time = (time.minute % self.frequency) + (time.second / 60)
        return elapsed_time < self.duration


class Before_DawnDuskTimeInterval(types.RecordingSavingFilter):
    """A before dawn and dusk time RecordingSavingFilter."""

    def __init__(self, duration: float, timezone: datetime.tzinfo):
        """Initiatlise the Before Dawn & Dusk RecordingSavingFilter."""
        self.duration = duration
        self.timezone = timezone

    def should_save_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
    ) -> bool:
        """Save a recording if it falls within the specified interval, before dawn and dusk.

        Notes
        -----
        The dawn and dusk times are calculated using the `astral` library. The
        `sun` function returns the dawn and dusk times for a specific location, datetime
        and timezone. This information is used to determine the interval before dawn and dusk
        dusk, and whether the current recording falls within this interval.

        Examples
        --------
        >>> DawnTime GMT: 2024-01-01 07:26:00+00:00
        >>> DuskTime GMT: 2024-01-01 16:42:00+00:00
        >>> duration = 30
        >>> timezone = "Europe/London"

        >>> saving_filter = Before_DawnDuskTimeInterval(
        ...     duration, timezone
        ... )
        >>> recording = data.Recording(
        ...     datetime=datetime.datetime(
        ...         2024, 1, 1, 7, 0, 0, tzinfo=timezone
        ...     )
        ... )
        >>> assert saving_filter.should_save_recording(recording)
        True

        >>> saving_filter = Before_DawnDuskTimeInterval(
        ...     duration, timezone
        ... )
        >>> recording = data.Recording(
        ...     datetime=datetime.datetime(
        ...         2024, 1, 1, 17, 0, 0, tzinfo=timezone
        ...     )
        ... )
        >>> assert saving_filter.should_save_recording(recording)
        False
        """
        recording_time = recording.created_on.astimezone(self.timezone)

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
    """An after dawn and dusk time RecordingSavingFilter."""

    duration: float
    """The duration (in minutes) before dawn and dusk where recordings will be saved."""

    timezone: datetime.tzinfo
    """The timezone to use when determining dawntime and dusktime."""

    def __init__(self, duration: float, timezone: datetime.tzinfo):
        """Initiatlise the Before Dawn & Dusk RecordingSavingFilter."""
        self.duration = duration
        self.timezone = timezone

    def should_save_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
    ) -> bool:
        """Save a recording if it falls within the specified interval, after dawn and dusk.

        Notes
        -----
        The dawn and dusk times are calculated using the `astral` library. The
        `sun` function returns the dawn and dusk times for a specific location, datetime
        and timezone. This information is used to determine the interval after dawn and dusk
        dusk, and whether the current recording falls within this interval.

        Examples
        --------
        >>> DawnTime GMT: 2024-01-01 07:26:00+00:00
        >>> DuskTime GMT: 2024-01-01 16:42:00+00:00
        >>> duration = 30
        >>> timezone = "Europe/London"

        >>> saving_filter = After_DawnDuskTimeInterval(
        ...     duration, timezone
        ... )
        >>> recording = data.Recording(
        ...     datetime=datetime.datetime(
        ...         2024, 1, 1, 7, 0, 0, tzinfo=timezone
        ...     )
        ... )
        >>> assert saving_filter.should_save_recording(recording)
        False

        >>> saving_filter = After_DawnDuskTimeInterval(
        ...     duration, timezone
        ... )
        >>> recording = data.Recording(
        ...     datetime=datetime.datetime(
        ...         2024, 1, 1, 17, 0, 0, tzinfo=timezone
        ...     )
        ... )
        >>> assert saving_filter.should_save_recording(recording)
        True
        """
        recording_time = recording.created_on.astimezone(self.timezone)

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
    """A SavingThreshold RecordingSavingFilter."""

    saving_threshold: float
    """The score threshold to use."""

    def __init__(self, saving_threshold: float):
        """Initialise the RecordingSavingFilter."""
        self.saving_threshold = saving_threshold

    def has_confident_model_output(
        self, model_output: data.ModelOutput
    ) -> bool:
        """Determine if a model output has confident detections or tags.

        An output is considered confident if any of its detection score
        or classification tag score is greater than or equal to the threshold.

        Parameters
        ----------
        model_output : data.ModelOutput
            The model output of the recording containing detections and tags.

        Returns
        -------
        bool
            True if any detection or classification score is above the saving threshold.
            False if no detection or classification score is above the saving threshold.
        """
        if any(
            tag.confidence_score >= self.saving_threshold
            for tag in model_output.tags
        ):
            return True

        if any(
            detection.detection_score >= self.saving_threshold
            for detection in model_output.detections
        ):
            return True

        return False

    def should_save_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
    ) -> bool:
        """Save a recording if it contains any confident detections or tags."""
        if model_outputs is None:
            return False

        return any(
            self.has_confident_model_output(model_output)
            for model_output in model_outputs
        )


class DetectionTagValue(types.RecordingSavingFilter):
    """A RecordingSavingFilter that keeps recordings with specific tag values."""

    values: List[str]
    """The tag values to focus on."""

    def __init__(self, values: List[str]):
        """Initialise the RecordingSavingFilter."""
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
        """Save a recording if it contains any confident tag values."""
        if model_outputs is None:
            return False

        return any(
            self.has_confident_tagvalues(model_output)
            for model_output in model_outputs
        )


class DetectionTags(types.RecordingSavingFilter):
    """A RecordingSavingFilter that keeps recordings with selected tags.

    This filter will keep recordings that contain confident tag
    predictions that are in the tags list.
    """

    tags: List[data.Tag]
    """The tags to focus on."""

    saving_threshold: float
    """The score threshold to use."""

    def __init__(self, tags: List[data.Tag], saving_threshold: float = 0.5):
        """Initialise the RecordingSavingFilter."""
        self.tags = tags
        self.saving_threshold = saving_threshold

    def has_confident_tag(self, model_output: data.ModelOutput) -> bool:
        """Determine if a model output has a confident tag.

        An output is considered confident if any of its tags or detections
        have a score greater than or equal to the threshold.

        Parameters
        ----------
        model_output : data.ModelOutput
            The model output of the recording containing detections and tags.

        Returns
        -------
            bool
        """
        if any(
            tag.tag in self.tags
            and tag.confidence_score >= self.saving_threshold
            for tag in model_output.tags
        ):
            return True

        for detection in model_output.detections:
            if detection.detection_score < self.saving_threshold:
                continue

            for tag in detection.tags:
                if tag.tag not in self.tags:
                    continue

                if tag.confidence_score >= self.saving_threshold:
                    return True

        return False

    def should_save_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
    ) -> bool:
        """Save a recording if it contains any confident tags or detections."""
        if model_outputs is None:
            return False

        return any(
            self.has_confident_tag(model_output)
            for model_output in model_outputs
        )
