# Configuration

Once acoupi has been installed on a device, users have the ability to configure a pre-built program.
Acoupi comes with default configuration parameters, user can accept the default parameters or input their own parameters when setting up acoupi.
This is done through acoupi command line interface.

### Configuring acoupi program via the CLI.
The video shows how a user can configured an acoupi program using the command line interface. 
The prompt to use in the CLI to configure the default program is as follow: 

```bash
acoupi setup --program acoupi.programs.default
```

Based on the program configuration, a number of questions will be printed to a user. The keyboard letter `y` or the touch `Enter` is used to **accept** the default configuration. The keyboard letter `n` is used to **reject and modify** the default configuration of a pre-built program.


![type:video](../img/acoupi_configuration_default.mp4){: style='width: 100%'}

### Configuration Paramaters for acoupi default program.

The example below shows the configured parameters for the acoupi default program. 

Note that audio recordings have a duration of 10 seconds, occuring every 30 seconds between 4am and 11pm. 
However, recordings are only saved between 11am and 3pm as well as withing the 30 minutes time interval that is before and after dawn and dusk. 

The values of `0` for parameters `frequency_duration`, and `frequency_interval` indicates that this filter will not be used to save recordings. 

The database registering the functionment of acoupi tasks and the audio recordings files are saved on the home directory in a folder entitled `storages/`. 

!!! Example "> acoupi config get"
    ```json 
    {
        "dbpath": "/home/pi/storages/acoupi.db",
        "audio_dir": "/home/pi/storages/recordings",
        "timeformat": "%Y%m%d_%H%M%S",
        "timezone": "Europe/London",
        "microphone_config": {
          "device_name": "UltraMic 250K 16 bit r4",
          "samplerate": 250000,
          "audio_channels": 1
        },
        "audio_config": {
          "audio_duration": 10,
          "recording_interval": 30
        },
        "recording_schedule": {
          "start_recording": "04:00:00",
          "end_recording": "23:00:00"
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