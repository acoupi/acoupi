# Configuration

Once _acoupi_ has been installed on a device, users can configure a pre-built program.
_acoupi_ comes with default settings, which users can either accept or customise through the command line interface (CLI). 

## Configuring _acoupi_ programs via the CLI

- __default program__: The _acoupi default_ program is the most simplest program, handling only two tasks: recording and managing audio files.
- __connected program__: The _acoupi connected_ program extends the default program by adding messaging capabilities, allowing users to send messages to a remote server.

To select and configure your prefered _acoupi_ program,  use of the following commands:

!!! Example "CLI Command: _acoupi default_ program"

    ```bash
    acoupi setup --program acoupi.programs.default
    ```

!!! Example "CLI Command: _acoupi connected_ program"

    ```bash
    acoupi setup --program acoupi.programs.connected
    ```

Based on the selected program, users will be prompted with several questions during setup. 
To **accept** the default values, press the keyboard letter `y` or the key `Enter`. 
To **reject and modify** a setting, press the keyboard letter `n` and input a new value.

The video shows the configuration process for the _acoupi default_ program via the CLI.  

![type:video](../img/acoupi_configuration.mp4){: style='width: 100%'}

## Configuration Parameters

### acoupi.programs.default

Below is an example of the configured parameters for the _default_ program in JSON format.

Audio recordings have a duration of 10 seconds and occur every 30 seconds between 4am and 11pm.
However, recordings are only saved between 11am and 3pm, and during a 30-minute window before and after dawn and dusk.

The values `0` for `frequency_duration` and `frequency_interval` indicate that no frequency filter is applied to save recordings.

The database storing the execution of _acoupi_ tasks and recordings of audion files is located in the `storages/` folder in the home directory.

!!! Example "CLI Command: view program configuration after setup"

    ```bash
    acoupi config get
    ```

!!! Example "CLI Output: _acoupi config get_"

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

!!! Tip "How to modify a value after setup?"
    
    You can modify the value of a parameter after an _acoupi_ program has been set up. This can be necessary either due to
    a misconfiguration or to make changes to the current program. To modify a parameter, use the command:


    !!! Example "CLI Command: modify a configuration parameter after setup"

          ```bash
          acoupi config set --field <parameter_name> <new_value>
          ```

      Replace the _`parameter_name`_ with the full name of the parameter to modified. For example, to update the recording start time to 10am, the CLI command would be as follow:

    !!! Example "CLI Command: modify recording start time"

          ```bash
          acoupi config set --field recording.schedule_start 10:00:00
          ```

The table below provides detailed information about the parameters available when setting up _acoupi_ _default_ program.

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
| `recording_saving.frequency_duration` | int (min.) | 5 | Duration in minutes for storing recordings when using the frequency filter. | Set to zero if not using this parameter.|
| `recording_saving.frequency_interval` | int (min.) | 30 | eriodic interval in minutes between two periods of storing recordings. | Set to zero if not using this parameter. |

### acoupi.programs.connected

The _acoupi connected_ program extends the  _acoupi default_ program by adding configuration options for sending messages to a remote server. It retains all the settings from the _acoupi default_ program but introduces new parameters for network communication.

Messages can be sent using either the HTTP or MQTT protocol. At least one of these protocols must be configured. If neither protocol is setup, the program will raise an error. 

The messages and their statuses, indicating if they have been sent, and whether this was a success or a failure, are stored in a database called `messages.db`. By default, this file is located in the `storages/` folder in the home directory.

The `message_send_interval` parameter controls how frequently the _acoupi_ program checks for new messages to send (i.e., 120 seconds by default). Similarly, the `heartbeat_interval` determines how often a `heartbeat_message`is sent (i.e., 10 minutes by default).


!!! Example "CLI Output: _acoupi config get_"

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
          "password": "mqtt_password",
          "topic": "acoupi",
          "port": 1884,
          "timeout": 5
        },
      },
      "recording_saving": {},
    }
    ```

The table below provides detailed information about the supplementary parameters available when setting up _acoupi_ _connected_ program.

| Parameter | Type | Default Value | Definition | Comment |
|---|---|---|---|---|
| __Paths__| | | Configuration for file paths.| |
| `messaging.messages_db`| string | "/home/pi/storages/messages.db" | Path to the database file storing messages. | This .db keeps track of the messages to be sent to a remote server and their sending/receiving status. |
| __Messaging__| | | Configuration for sending messages to remote server.| Will require access to network connectivity at the location of your device deployment. |
| `messaging.message_send_interval`| int (sec.) | 120 | Interval in seconds for sending messages to the remote server. | Adjust for network performance and data bandwidth. |
| `messaging.heartbeat_interval` | int (sec.) | 600 | Interval in seconds for sending heartbeat messages to the server. | Heartbeat message provides information about the device status (i.e., the correct functioning of the device). |
| __Messaging HTTP__| | | Configuration for sending messages via HTTP.| |
| `messaging.http.base_url` | str | - | URL of the HTTP server to which messages are sent. | Configure according to your server setup. |
| `messaging.http.content_type` | str | application/json | Content type of the HTTP messages. | Messages to be sent are formated into a `json` object. |
| `messaging.http.timeout` | int (sec) | - | Timeout for HTTP requres in seconds.. | |
| __Messaging MQTT__| | | Configuration for sending messages via MQTT.| |
| `messaging.mqtt.host` | str | - | MQTT server hostname for message transmission. | Configure according to your server setup. |
| `messaging.mqtt.username` | str | - | Username for authentication with the MQTT broker. | Replace with your server username. |
| `messaging.mqtt.password` | str | - | Password for authentication with the MQTT broker. | Replace with your server password. |
| `messaging.mqtt.topic` | str | "acoupi" | Topic on the MQTT broker to publish messages | Replace with your server setup. |
| `messaging.mqtt.port`| int | 1884 |  Port number of the MQTT broker. | Default port is usually fine unless other setup on your server. |
| `messaging.mqtt.timeout` | int (sec) | 5 | Timeout for connecting to the MQTT broker in seconds. | |