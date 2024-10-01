# Configuration

Once acoupi has been installed on a device, users have the ability to configure a pre-built program.
Acoupi comes with default configuration parameters, user can accept the default parameters or input their own parameters when setting up acoupi.
This is done through acoupi command line interface.

_Add image of acoupi CLI parameters._

### Configuring acoupi program via the CLI.

### Configuration Paramaters for acoupi default program.

The example below show the configured parameters for the acoupi default program. 

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