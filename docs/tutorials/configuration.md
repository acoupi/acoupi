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

### Overview Configuration Parameters

#### acoupi paramaters description


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

  
The table below provides detailed information about the parameters available for configuration when using the _acoupi_ __default program__.

| Parameter | Type | Default Value | Definition | Comment |
|---|---|---|---|---|
| __Microphone__| | | Microphone configuration.| |
| `microphone.device_name`| string | - | Will show the name of the connected usb microphone.| Ensure it matches the device in use.|
| `microphone.samplerate`| int (Hz) | - | Sampling rate of the microphone in Hz. | Set the sampling rate according to the microphone's specifications.|
|`microphone.audio_channels`| int | - | Number of audio channels (i.e., 1 for mono).| Configure according to the microphone's capabilities.|
| __Recording__| | | Microphone configuration.| |
| `recording.duration`| int (sec.) | 3 | Duration in seconds for each audio recording. | Best kept at 3 seconds when using acoupi with ML classifiers models (e.g., batdetect2, birdnet) for optimal performance.|
| `recording.interval`| int (sec.) | 12 | Interval in seconds between recordings. | Some pre-built programs with ML models (e.g., batdetect2) require processing time. This interval helps maintain good performance.|
| `recording.chunksize`| int | 8192 | Chunksize of the audio recording.| An error will occur if the chunksize is too small for the audio device. |
| `schedule_start`| time (HH:MM:SS)| 06:00:00 | Time of day when recordings will start (24-hour format).| Adjust according to specific monitoring needs (e.g., nightime hours). |
| `schedule_end`| time (HH:MM:SS)| 18:00:00 | Time of day when recordings will end (24-hour format). | Adjust according to specific monitoring needs (e.g., nightime hours). |
| `timezone`| string | "Europe/London" | Timezone of the sensor location. | Configure this according to your deployment region.|
| __Paths__| | | Configuration for file paths.| |
| `paths.tmp_audio`| string | "/run/shm" | Temporary storage path for audio recordings. | Temporary in-memory path. Do not modify. |
| `paths.recordings`| string | "/home/pi/storages/recordings" | Path to directory storing recorded audio files.| Modify accordingly. With default paths, recordings are stored on the SDCard, modify if using external usb hardrive. |
| `paths.db_metadata`| string | "/home/pi/storages/metadata.db" | Path to the database file storing the metadata. | This .db keeps track of recorded files, ML detection results, and system information. |
| __Recording Saving (Optional)__ | N/A | - | Configuration for saving recorded audio files. | |
| `recording_saving.starttime`| time (HH:MM:SS)| "18:30:00"| Start time for saving recorded audio files (24-hour format).| Insert 00:00:00 to not use this parameter to save audio recordings.|
| `recording_saving.endtime`| time (HH:MM:SS)| "20:00:00"| End time for saving recorded audio files (24-hour format)| Insert 00:00:00 to not use this parameter to save audio recordings. |
| `recording_saving.before_dawndusk_duration` | int (min.) | 10 | Additional duration (in minutes) to save recordings __before__ the dawn/dusk time.| Ensure recording interval covers the dawn and dusk time if using this parameter. |
| `recording_saving.after_dawndusk_duration`  | int (min.) | 10 |  Additional duration (in minutes) to save recordings __after__ the dawn/dusk time.| Ensure recording interval covers the dawn and dusk time if using this parameter. |
| `recording_saving.frequency_duration` | int (min.) | 0 | Length of time in minutes to save recordings for if using frequency based saving paramters.| Set to zero if not using this parameter.|
| `recording_saving.frequency_interval` | int (min.) | 0 | Interval duration in minutes between period of time to save recordings. | Set to zero if not using this parameter. |


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

The table below provides detailed information about the supplementary parameters available for configuration when using the _acoupi_ __connected program__.

| Parameter | Type | Default Value | Definition | Comment |
|---|---|---|---|---|
| __Paths__| | | Configuration for file paths.| |
| `messaging.messages_db`| string | "/home/pi/storages/messages.db" | Path to the database file storing messages. | This .db keeps track of the messages to be sent to a remote server and their sending/receiving status. |
| __Messaging (Optional)__| | | Configuration for sending messages to remote server.| Will require access to network connectivity at the location of your device deployment. |
| `messaging.message_send_interval`| int (sec.) | 120 | Interval in seconds for sending messages to the remote server. | Adjust for network performance and data bandwidth. |
| `messaging.heartbeat_interval` | int (sec.) | 600 | Interval in seconds for sending heartbeat messages to the server. | Heartbeat message provides information about the device status (i.e., the correct functioning of the device). |
| `messaging.mqtt.host` | string | - | MQTT server hostname for message transmission. | Configure according to your server setup. |
| `messaging.mqtt.username` | string | - | Username for authentication with the MQTT broker. | Replace with your server username. |
| `messaging.mqtt.password` | string | - | Password for authentication with the MQTT broker. | Replace with your server password. |
| `messaging.mqtt.topic` | string | "acoupi" | Topic on the MQTT broker to publish messages | Replace with your server setup. |
| `messaging.mqtt.port`| int | 1884 |  Port number of the MQTT broker. | Default port is usually fine unless other setup on your server. |
| `messaging.mqtt.timeout` | int (sec) | 5 | Timeout for connecting to the MQTT broker | |