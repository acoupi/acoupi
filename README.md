# acoupi

> [!TIP]
> Read the latest [documentation](TODO: Add Link to documentation)

## What is acoupi? 
**acoupi** is an open-source python software to facilitate the deployment of bioacoustic classifiers on edge devices like the Raspberry Pi. It includes individual components for audio recordings, audio processing, audio classifications and detections, results communication, and audio files and results management. **Acoupi** integrates and standardises the entire workflow of biacoustic monitoring, combining both autonomous recording and classification units. 

- [Requirements](#requirements)
- [Installation](#installation)
- [Default components of acoupi](#default-components-of-acoupi)
- [Pre-build programs in acoupi](#pre-build-programs-in-acoupi)
- [Features and development](#features)

## Requirements

- A Linux-based single board computer such as the Raspberry Pi 4B. 
- A SD Card with 64-bit Lite OS version installed.
- A USB Microphone such as an AudioMoth, a µMoth an Ultramic 192K.

## Installation

To install and use acoupi on your embedded device follow these steps: 

Step 1: Install acoupi and its dependencies
```
wget -O- https://raw.githubusercontent.com/audevuilli/acoupi/master/install.sh | bash
```

Step 2: Configure one of acoupi pre-built programs - replace `program-name` with `batdetect2` or `birdnet`. 

By running this command, you will be promted with a serie of question to configure the program. For more details about the configuration options, please refere to *[Acoupi Documentation: Configuration Options](TODO: Add Link to Configuration Options in Documentation)*

```
    pdm run acoupi setup `program-name`
```
Step 3: To check if the installation was successful, run the following command:
```
pdm run acoupi --help
```

Step 4: To start acoupi run the command: 
```
pdm run acoupi start
```

## Default components of acoupi

1.  [**RecordingScheduler**](src/acoupi/recording_schedulers.py): Define how often recordings should be made. The class `IntervalScheduler` derived from RecordingScheduler uses an argument called `DEFAULT_RECORDING_INTERVAL` to set a time interval in second.
2. [**RecordingCondition**](src/acoupi/recording_conditions.py): Define the specific time that recordings should be made. The class `IsInIntervals` derived from RecordingCondition uses two arguments `START_TIME` and `END_TIME` to specify the recording conditions. The conditions tell the system whether or not to record audio files. 
3. [**AudioRecorder**](src/acoupi/audio_recorder.py): Define how to record audio files. The class `PyAudioRecorder` derived from AudioRecorder configures the parameters of recordings. It uses multiple arguments such as the recording duration `DEFAULT_RECORDING_DURATION` and sample rate `DEFAULT_SAMPLERATE`, and the number of audio_channels `DEFAULT_AUDIO_CHANNELS`. 
4. [**Model**](src/acoupi/model.py): Define the model that is employed to analyse audio recordings. Here, the class `BatDetect2` refers to the BatDetect2 model that detect bat calls and identify the related bat species of the audio recordings. The class BatDetect2 takes an audio recording (the output of the method `record()` from the class `PyAudioRecorder`).
5. **[SaveRecordingFilter](src/acoupi/recording_filters.py) & [DetectionFilter](src/acoupi/detection_filters.py)**: Define the conditions that determine how a recording and its associated detections should be saved such as recording and detections that meet a probability threshold criteria and a specific species. For our BatDetect2 implementation, we use the classes `ThresholdRecordingFilter` and `ThresholdDetectionFilter`. Both classes require a threshold argument called `DEFAULT_THRESHOLD`. This argument is used to determine whether any detections are found above (return TRUE) or below  (return FALSE) the specifed threshold.
6. [**SaveRecordingManager**](src/acoupi/saving_managers.py): Responsible for saving the recording and the associated detections. The SavingManager contains three classes `Directories`, `SaveRecording` and `SaveDetection`. The Directories class takes two arguments: `DIR_TRUE` and `DIR_FALSE`. These arguments specify the directories in which the recordings and detections should be saved, depending on the result of the recording and detection filters. The SaveRecording and SaveDetection classes take a `DEFAULT_TIMEFORMAT` argument, which specifies the datetime format to use for the file name of the saved recording and detection. 

## Pre-build programs in acoupi

## Features and development



## Diagram

![diagram](docs/old_docs/acoupi-processdiagram.png)

## Running BatDetect2

The implementation of BatDetect2 is based on components defined in Acoupi. To test a basic deployment of BatDetect2, various acoupi components are implemented. These consist of the following: 

### Modify Arguments in BatDetect2

**Acoupi-BatDetect2** comes with a range of configurable arguments that can be used to adjust the behaviour of the acoustic monitoring system. These arguments are defined in a file called [`config.py`](src/acoupi/config.py). By changing the value of an arugment, such as `DEFAULT_THRESHOLD`, the seystem will use the new value in place of the default value. 

It is important to note that the argument names should not be changed, as doing so will require modifications to the [`main.py`](src/acoupi/main.py) file. 

To modify an argument, simply locate the relevant argument `config.py`and change the value to the new desired value. For example, to adjust the threshold of the detection filters, you can change the value of `DEFAULT_THRESHOLD` to a higher or lower value. By modifying the arguments, you can fine-tune the behaviour of Acoupi-BatDetect2 to better suit your specific needs and requirements. 

## Development

### Package dependencies

We are using [pdm](https://pdm.fming.dev/latest/) to manage package dependencies. In order to install the package and all dependencies (including the development dependencies) run the command

    pdm install
  
To add a dependencies to the package run

    pdm add <dependency1> ...
  
make sure to commit and uplaod both the changes to the pyproject.toml file and the pdm.lock.

To add development-only dependencies run

    pdm add -d <dev_dependency1> ...

### Testing

We are using [pytest](https://docs.pytest.org/en/7.2.x/) as a test runner. All tests are in the `test` directory. To run the suite of tests run the command

    pdm run pytest
  
 Running through `pdm` will insure that the acoupi package and all its dependencies are loaded before running the tests.
