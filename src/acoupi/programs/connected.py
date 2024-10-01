"""Acoupi Connected Program.

This program provides a basic Acoupi program with added messaging
capabilities. It combines the features of the `BasicProgramMixin` and
`MessagingProgramMixin` templates to create a program that can record audio,
store metadata, manage files, and send messages and heartbeats.

Features:

- **Audio Recording:** Records audio clips at regular intervals.
- **Metadata Storage:** Stores metadata associated with recordings in a
  SQLite database.
- **File Management:** Manages the storage of audio recordings, saving them to
  permanent storage and handling temporary files.
- **Messaging:** Sends messages and heartbeats to a configured messenger
  (HTTP or MQTT).

Configuration:

The program's configuration is defined by the `ConfigSchema`, which inherits
from `BasicConfiguration` and `MessagingConfigMixin`. This schema includes
settings for:

- **Basic Program:**
    - Timezone
    - Microphone configuration
    - Audio recording settings (duration, interval, schedule)
    - Data storage locations (temporary directory, audio directory, metadata
                              database)
- **Messaging:**
    - Message database location
    - Message sending interval
    - Heartbeat interval
    - Messenger configuration (HTTP or MQTT)

Usage:

To use the Connected Program, run the setup with acoupi:

```bash
acoupi setup --program acoupi.programs.connected
```

and follow the setup wizard.

Once the program is configured, start it with:

```bash
acopi deployment start
```

The program will then start recording audio, storing metadata, managing files,
and sending messages and heartbeats according to the configured settings.
"""

import datetime
from typing import Optional

import pytz
from pydantic import BaseModel

from acoupi import components, data
from acoupi.programs import AcoupiProgram
from acoupi.programs.templates import (
    BasicConfiguration,
    BasicProgramMixin,
    MessagingConfigMixin,
    MessagingProgramMixin,
)


class SaveRecordingFilter(BaseModel):
    """Recording saving options configuration."""

    starttime: datetime.time = datetime.time(hour=18, minute=30, second=0)

    endtime: datetime.time = datetime.time(hour=20, minute=0, second=0)

    before_dawndusk_duration: int = 10

    after_dawndusk_duration: int = 10

    frequency_duration: int = 5

    frequency_interval: int = 5


class ConfigSchema(BasicConfiguration, MessagingConfigMixin):
    """Configuration Schema for Connected Program.

    This schema combines the settings for basic program functionality and
    messaging capabilities.
    """

    recording_saving: Optional[SaveRecordingFilter] = None


class Program(MessagingProgramMixin, BasicProgramMixin, AcoupiProgram):
    """Connected Program.

    This program provides a basic Acoupi program with added messaging
    capabilities.
    """

    config_schema = ConfigSchema

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
            recording_saving.frequency_duration is not None
            and recording_saving.frequency_interval is not None
        ):
            # This filter will only save recordings at a frequency defined
            # by the duration and interval.
            saving_filters.append(
                components.FrequencySchedule(
                    duration=recording_saving.frequency_duration,
                    frequency=recording_saving.frequency_interval,
                )
            )

        if recording_saving.before_dawndusk_duration is not None:
            # This filter will only save recordings if the recording time
            # is before dawn or dusk.
            saving_filters.append(
                components.Before_DawnDuskTimeInterval(
                    duration=recording_saving.before_dawndusk_duration,
                    timezone=timezone,
                )
            )

        if components.After_DawnDuskTimeInterval is not None:
            # This filter will only save recordings if the recording time
            # is after dawn or dusk.
            saving_filters.append(
                components.After_DawnDuskTimeInterval(
                    duration=recording_saving.after_dawndusk_duration,
                    timezone=timezone,
                )
            )

        return saving_filters
