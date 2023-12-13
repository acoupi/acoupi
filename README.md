# acoupi

> [!TIP]
> Read the latest [documentation](TODO: Add Link to documentation)

## What is acoupi? 
**acoupi** is an open-source Python software package to facilitate the deployment of bioacoustic classifiers on edge devices like the Raspberry Pi. It includes individual components for audio recordings, audio processing, audio classifications and detections, results communication, and audio files and results management. **Acoupi** integrates and standardises the entire workflow of biacoustic monitoring, combining both autonomous recording and classification units. 

- [Requirements](#requirements)
- [What is acoupi? Acoupi software architecture.](#acoupi-software-architecture)
- [Pre-built AI bioacoustics classifiers](#pre-built-ai-bioacoustics-classifiers)
- [Features and development](#features)
- [Installation](#installation)

## Requirements

- A Linux-based single board computer such as the Raspberry Pi 4B. 
- A SD Card with 64-bit Lite OS version installed.
- A USB Microphone such as an AudioMoth, a µMoth an Ultramic 192K.

## Acoupi Software Architecture

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

## Pre-built AI Bioacoustics Classifiers

With acoupi, our aim is to facilitate the use and implementation of open-source AI bioacoustics models. We currently provide the configuration for two modelds [BatDetect2]((https://github.com/macaodha/batdetect2) developed by [@macodha and al.](https://doi.org/10.1101/2022.12.14.520490) and [BirdNET-Lite](https://github.com/kahst/BirdNET-Lite) developed by [@kahst and al.](https://github.com/kahst).

### BatDetect2

The [`BatDetect2`](https://github.com/macaodha/batdetect2) AI Detection Model for UK bats species is installed and configured in the [`acoupi_batdetect2`](https://github.com/acoupi/acoupi_batdetect2) GitHub folder. If you wish to use acoupi to record and detect bats in the UK. You can directly install it and configure it using the commands: 
```
pip install acoupi_batdetect2
acoupi setup --program acoupi_batdetect2.program.batdetect2
```

### BirdNET-Lite

The `BirdNET-Lite` AI Detection Model for UK bats species is installed and configured in the [`acoupi_birdnet`](https://github.com/acoupi/acoupi_birdnet) GitHub folder. If you wish to use acoupi to record and detect bats in the UK. You can directly install it and configure it using the commands: 
```
pip install acoupi_batdetect2
acoupi setup --program acoupi_birdnet.program.birdnet
```

## Features and development
**acoupi** builds on other Python packages. The list of the most important packages and their functions is summarised below. For more information about each of them, make sure to check their respective documentation. 
- [PDM](https://pdm-project.org/2.10/) to manage package dependencies. 
- [Pydantic](https://docs.pydantic.dev/dev/) for data validation. 
- [Pytest](https://docs.pytest.org/en/7.4.x/) as a testing framework.
- [Pony-ORM](https://ponyorm.org/) for databse queries. 
- [Celery](https://docs.celeryq.dev/en/stable/getting-started/introduction.html) to manage the processing of tasks. 
- [Jinja](#jinja) for text templating. 

## Acoupi Installation

> [!IMPORTANT]
> To install one of the acoupi pre-built programs containing either the `BatDetect2` or the `BirdNET-Lite` bioacoustics classifiers, refer to the information in the above section:  [Pre-built AI bioacoustics classifiers](#pre-built-ai-bioacoustics-classifiers).


To install and use the bare-bone framework of acoupi on your embedded device follow these steps: 

**Step 1:** Install acoupi and its dependencies
```
pip install acoupi
```
**Step 2:** Configure acoupi default program. (*acoupi comes with a test and a default program. The default program is only recording and saving audio files based on the users' settings. Think like something similar to the setup of an AudioMoth*). 
```
acoupi setup --program `program-name`
```
For acoupi default program, enter this command: 
```
acoupi setup --program acoupi.programs.custom.acoupi
```
**Step 3:** To start acoupi run the command: 
```
acoupi start
```

>[!TIP]
> To check what are the available commands for acoupi, enter:
>```
> acoupi --help
>```
