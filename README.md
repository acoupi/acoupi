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

**Step 1:** Install acoupi and its dependencies
```
wget -O- https://raw.githubusercontent.com/audevuilli/acoupi/master/install.sh | bash
```

**Step 2:** Configure one of acoupi pre-built programs - replace `program-name` with `batdetect2` or `birdnet`. 

By running this command, you will be promted with a serie of question to configure the program. For more details about the configuration options, please refere to *[Acoupi Documentation: Configuration Options](TODO: Add Link to Configuration Options in Documentation)*

```
(pdm run) acoupi setup --program `program-name`
```
**Step 3:** To check if the installation was successful, run the following command:
```
(pdm run) acoupi --help
```

**Step 4:** To start acoupi run the command: 
```
pdm run acoupi start
```

## Acoupi Buildling Blocks

**acoupi** is built following a structure of 4 layers: program, tasks, components and data schema. Users of **acoupi** will principally interact with the program layers, while developers will likely interact with the other layers. 

Below we provide an overview of the 4 layers of acoupi. This is not to scare users but mostly to illustrate the modulariy and flexibilty of around acoupi building blocks. 

![Figure 1: Overview of acoupi layers](/docs/img/acoupi_buildingblocks.png)
*Figure 1: Overview of acoupi layers*

![Figure 2: Example of Acoupi Flow of Information](/docs/img/acoupi_flowchart_img.png)
*Figure 2: Example of Acoupi Flow of Information*

Acoupi components form the building blocks of acoupi. Each component has a single responsibility and performs a specific action. 

1. [**RecordingConditions**](src/acoupi/components/recording_conditions.py): Define the specific time that recordings should be made. The class `IsInIntervals` derived from RecordingCondition uses two arguments `START_TIME` and `END_TIME` to specify the recording conditions. The condions tell the system whether or not to record audio files. 
1. [**RecordingSchedulers**](src/acoupi/components/recording_schedulers.py): Define how often recordings should be made. The class `IntervalScheduler` derived from RecordingSchedulers uses an argument called `DEFAULT_RECORDING_INTERVAL` to set a time interval in second.
3. [**AudioRecorders**](src/acoupi/components/audio_recorder.py): Define how to record audio files. The class `PyAudioRecorder` derived from AudioRecorder configures the parameters of recordings. It uses multiple arguments such as the recording duration `DURATION`, the sample rate `SAMPLERATE`, the number of audio_channels `AUDIO_CHANNELS`, the device index `DEVICE_INDEX` and the audio chunk lenght `AUDIO_CHUNK`. 
4. [**Models**](src/acoupi/components/models.py): Define the model that is employed to analyse audio recordings. Here, the class name refers to the bioacoustics model name that detect, classify or identify related species in audio recordings. Acoupi comes with two pre-built models [`BatDetect2`](https://github.com/macaodha/batdetect2) for UK Bat species detection and [`BirdNET`](https://github.com/kahst/BirdNET-Lite) for bird species classification. The `Model` class takes an audio recording (the output of the method `record()` from the class `PyAudioRecorder`).
5. **[ProcessingFilters](src/acoupi/components/processing_filters.py) & [OutputCleaners](src/acoupi/components/output_cleaners.py)**: Define the conditions that determine how a recording and its associated detections should be saved such as recording and detections that meet a probability threshold criteria and a specific species. We implemented the classes `ThresholdRecordingFilter` and `ThresholdDetectionFilter`. Both classes require a threshold argument called `DEFAULT_THRESHOLD`. This argument is used to determine whether any detections are found above (return TRUE) or below (return FALSE) the specifed threshold.
6. [**SavingFilters**](src/acoupi/components/saving_filters.py): Responsible for saving the audio recordings. The SavingFilters class is optional. It allows a user to save audio recording files on a SD Card. The SavingFilters implemented many subclasses to allow for specific use cases. Examples of classes are `Before_DawnDusk`and `After_DawnDusk`, `Detection_Threshold`, `FrequencySchedule`, and `Start_Time` and `End_Time`. The SaveRecordingFilters classes take a `TIMEFORMAT` argument, which specifies the datetime format to use for the file name. 

## Pre-build programs in acoupi

### BatDetect2

### BirdNET-Lite

## Features and development
**acoupi** builds on other Python packages. The list of the most important packages and their functions is summarised below. For more information about each of them, make sure to check their respective documentation. 
- [PDM](https://pdm-project.org/2.10/) to manage package dependencies. 
- [Pydantic](https://docs.pydantic.dev/dev/) for data validation. 
- [Pytest](https://docs.pytest.org/en/7.4.x/) as a testing framework.
- [Pony-ORM](https://ponyorm.org/) for databse queries. 
- [Celery](https://docs.celeryq.dev/en/stable/getting-started/introduction.html) to manage the processing of tasks. 
- [Jinja](#jinja) for text templating. 

### PDM Python Library

We are using [pdm](https://pdm.fming.dev/latest/) to manage package dependencies. In order to install the package and all dependencies (including the development dependencies) run the command:
```
pdm install
```
  
To add a dependencies to the package run:

    pdm add <dependency1> ...
  
make sure to commit and uplaod both the changes to the pyproject.toml file and the pdm.lock.

To add development-only dependencies run:

    pdm add -d <dev_dependency1> ...

### Testing

We are using [pytest](https://docs.pytest.org/en/7.2.x/) as a test runner. All tests are in the `test` directory. To run the suite of tests run the command

    pdm run pytest
  
 Running through `pdm` will insure that the acoupi package and all its dependencies are loaded before running the tests.


