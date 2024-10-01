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

from acoupi.programs import AcoupiProgram
from acoupi.programs.templates import (
    BasicConfiguration,
    BasicProgramMixin,
    MessagingConfigMixin,
    MessagingProgramMixin,
)


class ConfigSchema(BasicConfiguration, MessagingConfigMixin):
    """Configuration Schema for Connected Program.

    This schema combines the settings for basic program functionality and
    messaging capabilities.
    """


class Program(MessagingProgramMixin, BasicProgramMixin, AcoupiProgram):
    """Connected Program.

    This program provides a basic Acoupi program with added messaging
    capabilities.
    """

    config_schema = ConfigSchema
