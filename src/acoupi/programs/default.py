"""Acoupi Default Program.

This is the most basic acoupi program. It only records audio files and does not
do any processing and messaging.
"""

import datetime
from typing import Optional

import pytz
from pydantic import BaseModel

from acoupi import components, data
from acoupi.programs.templates import BasicProgram, BasicProgramConfiguration


class SaveRecordingFilter(BaseModel):
    """Recording saving options configuration."""

    starttime: datetime.time = datetime.time(hour=18, minute=0, second=0)

    endtime: datetime.time = datetime.time(hour=20, minute=0, second=0)

    before_dawndusk_duration: int = 10

    after_dawndusk_duration: int = 10

    frequency_duration: int = 5

    frequency_interval: int = 30


class ConfigSchema(BasicProgramConfiguration):
    """Configuration Schema for Test Program."""

    recording_saving: Optional[SaveRecordingFilter] = None


class Program(BasicProgram):
    """Test Program."""

    config_schema = ConfigSchema

    ### --- Configure Additional Filters - SavingRecordingFilters --- ###
    def get_recording_filters(self, config: ConfigSchema):
        if not config.recording_saving:
            # No saving filters defined
            return []

        saving_filters = []
        timezone = pytz.timezone(config.timezone)
        recording_saving = config.recording_saving

        # Main filter
        # Will only save recordings if the recording time is in the
        # interval defined by the start and end time.
        if (
            recording_saving.starttime is not None
            and recording_saving.endtime is not None
        ):
            saving_filters.append(
                components.SaveIfInInterval(
                    interval=data.TimeInterval(
                        start=recording_saving.starttime,
                        end=recording_saving.endtime,
                    ),
                    timezone=timezone,
                )
            )

        # Additional filters
        if (
            recording_saving.frequency_duration != 0
            and recording_saving.frequency_interval != 0
        ):
            # This filter will only save recordings at a frequency defined
            # by the duration and interval.
            saving_filters.append(
                components.FrequencySchedule(
                    duration=recording_saving.frequency_duration,
                    frequency=recording_saving.frequency_interval,
                )
            )

        if recording_saving.before_dawndusk_duration != 0:
            # This filter will only save recordings if the recording time
            # is before dawn or dusk.
            saving_filters.append(
                components.Before_DawnDuskTimeInterval(
                    duration=recording_saving.before_dawndusk_duration,
                    timezone=timezone,
                )
            )

        if recording_saving.after_dawndusk_duration != 0:
            # This filter will only save recordings if the recording time
            # is after dawn or dusk.
            saving_filters.append(
                components.After_DawnDuskTimeInterval(
                    duration=recording_saving.after_dawndusk_duration,
                    timezone=timezone,
                )
            )

        return saving_filters
