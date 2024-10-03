# Configuration

Once _acoupi_ has been installed on a device, users have the ability to configure a pre-built program.
_acoupi_ comes with default configuration parameters, user can accept the default parameters or input their own parameters when setting up _acoupi_.
This is done through _acoupi_ command line interface.

### Configuring _acoupi_ program via the CLI.

The video shows how a user can configure an _acoupi_ program using the command line interface.
The command to use in the CLI to configure the default program is as follow:

```bash
acoupi setup --program acoupi.programs.default
```

Based on the program configuration, a number of questions will be presented to the user.
The keyboard letter `y` or the touch `Enter` is used to **accept** the default configuration.
The keyboard letter `n` is used to **reject and modify** the default configuration of a pre-built program.

![type:video](../img/acoupi_configuration.mp4){: style='width: 100%'}

### Configuration Parameters

#### acoupi.programs.default

The example below shows the configured parameters for the _acoupi_ _default_ program in JSON format.

Note that audio recordings have a duration of 10 seconds, occurring every 30 seconds between 4am and 11pm.
However, recordings are only saved between 11am and 3pm as well as within the 30 minutes time interval that is before and after dawn and dusk.

The values of `0` for parameters `frequency_duration`, and `frequency_interval` indicates that this filter will not be used to save recordings.

The database registering the functioning of _acoupi_ tasks and the audio recordings files are saved on the home directory in a folder titled `storages/`.

!!! Example "> acoupi config get"

    ```json
    {
      "timezone": "Europe/London",
        "microphone": {
          "device_name": "UltraMic 250K 16 bit r4",
          "samplerate": 250000,
          "audio_channels": 1
      },
      "recording": {
        "duration": 10,
        "interval": 30,
        "chunksize": 8192,
        "schedule_start": "04:00:00",
        "schedule_end": "23:00:00"
      },
      "paths": {
        "tmp_audio": "/run/shm",
        "recordings": "/home/pi/storages/recordings",
        "db_metadata": "/home/pi/storages/metadata.db"
      },
      "recording_saving": {
        "starttime": "11:00:00",
        "endtime": "15:00:00",
        "before_dawndusk_duration": 30,
        "after_dawndusk_duration": 30,
        "frequency_duration": 0,
        "frequency_interval": 0
      }
    }
    ```

#### acoupi.programs.connected

The example below shows the added parameters for the _acoupi_ _connected_ program.

This program comes with a messaging section to configure the parameters to the send messages to a remote server.
The messages to be sent and their associated status is stored in a database named `messages.db` on the home directory in a folder titled `storages/`.
The value of `message_send_interval` indicates that messages will be sent every 120 seconds, while the `heartbeat_interval` indicates that `heartbeat_message` are sent every 10 minutes.
Messages are sent via the HTTP and MQTT protocols.

!!! Example "> acoupi config get"

    ```json
    {
      "recording": {},
      "paths": {},
      "messaging": {
        "messages_db": "/home/pi/storages/messages.db",
        "message_send_interval": 120,
        "heartbeat_interval": 600,
        "http": {
          "base_url": "https://test_acoupi.org/",
          "content_type": "application/json",
          "timeout": 5
        },
        "mqtt": {
          "host": "test_acoupi.mqtt.org",
          "username": "test_username",
          "password": "**********",
          "topic": "acoupi",
          "port": 1884,
          "timeout": 5
        },
      },
      "recording_saving": {},
    }
    ```
