# acoupi

> [!TIP]
> Read the latest [documentation](https://acoupi.github.io/acoupi/)

#### Readme Content
- [What is acoupi?](#what-is-acoupi)
- [Requirements](#requirements)
- [Installation](#installation)
- [Acoupi software architecture](#acoupi-software-architecture)
    - [Framework](#acoupi-framework)
    - [Application](#acoupi-application)
- [Pre-built AI Classifiers](#pre-built-ai-bioacoustics-classifiers)
- [Features](#features)

## What is acoupi? 
**acoupi** is an open-source Python software package to facilitate the deployment of bioacoustic classifiers on edge devices like the Raspberry Pi. It includes individual components for audio recordings, audio processing, audio classifications and detections, results communication, and audio files and results management. **acoupi** integrates and standardises the entire workflow of biacoustic monitoring, combining both autonomous recording and classification units. The figure below illustrates how **acoupi** software fits in the toolbox of bioacoustic researchers. 

![Figure 1: Overview of where the acoupi software package fits in the toolbox of bioacoustics research](/docs/img/acoupi_software_overview.jpeg)
***Figure 1: An overview of acoupi software.** The software is made of four tasks (i.e., audio recording, edge processing, wireless transfer, and data management and storage). Acoupi sits at the core of the bioacoustics research toolbox. Acoupi provides functionalities for users to define their own configurations, select their own audio classifiers (e.g., existing pre-built DL models), and build network endpoints to third-party apps (e.g., data visualisations tools and remote data backup).*

## Requirements
Acoupi has been designed to run on single-board computer devices like the RPi. The software has been extensively developed and tested with the RPi 4B. We advise users to select the RPi 4B or a device featuring similar specifications. 

Users should be able to download and test acoupi software on any Linux-based machines with Python version >=3.8,<3.12 installed. 

- A Linux-based single board computer such as the Raspberry Pi 4B. 
- A SD Card with 64-bit Lite OS version installed.
- A USB Microphone such as an AudioMoth, a µMoth, an Ultramic 192K/250K.

## Installation
> [!IMPORTANT]
> To install one of the acoupi pre-built programs containing either the **BatDetect2** or the **BirdNET-Lite** bioacoustics classifiers, refer to the information in the below section: [Pre-built AI bioacoustics classifiers](#pre-built-ai-bioacoustics-classifiers).

**The following steps will install the bare-bone architecture of acoupi on your embedded device.** 

### Step 1: Install acoupi and its dependencies.
```
pip install acoupi
```
### Step 2: Setup acoupi program configuration. 
```
acoupi setup --program `program-name`
```

> [!IMPORTANT]
> acoupi comes with a **test program** and a **default program**. The default program only records and saves audio files based on a user settings. The default program can be compared to setting up an AudioMoth. 

From the above command, replace **'program-name'** with **acoupi_default.program** or **acoupi_test.program** to select the one you want to use. The command for the **default program** will be as follow:
```
acoupi setup --program acoupi.custom.acoupi
```
 ### Step 3: Check acoupi program has been configured correctly.
```
acoupi check
```
 ### Step 4: Start running your configured program.
```
acoupi deployment start
```

> [!TIP]
> To check what are the available commands for acoupi, enter `acoupi --help`.

## Pre-built AI Bioacoustics Classifiers

With acoupi, we aim to facilitate the use and implementation of open-source AI bioacoustics models. We currently provide the configuration for two bioacoustics classifers; the [**BatDetect2**](https://github.com/macaodha/batdetect2) developed by [@macodha and al.](https://doi.org/10.1101/2022.12.14.520490) and the [**BirdNET-Lite**](https://github.com/kahst/BirdNET-Lite) developed by [@kahst and al.](https://github.com/kahst).

> [!IMPORTANT]
> **Please make sure you are aware of their license, if you use these models.**

### BatDetect2

The BatDetect2 bioacoustics DL model has been trained to detect and classify **UK bats species**. The [**acoupi_batdetect2**](https://github.com/acoupi/acoupi_batdetect2) repository provides users with a pre-build acoupi program that can be configured and tailored to their use cases. 

The program can directly be installed and configured typing the two following commands in a CLI.
```
pip install acoupi_batdetect2
acoupi setup --program acoupi_batdetect2.program
```

### BirdNET-Lite

The BirdNET-Lite bioacoustics DL model has been trained to detect and classify a large number of bird species. The [**acoupi_birdnet**](https://github.com/acoupi/acoupi_birdnet) repository provides users with a pre-build acoupi program that can be configured and tailored to their use cases of birds monitoring. 

The program can directly be installed and configured by typing the two following commands in a CLI: 
```
pip install acoupi_birdnet
acoupi setup --program acoupi_birdnet.program
```

## Acoupi Software

Acoupi software is divided into two parts; the code-based architecture and the running application. The ***acoupi architecture*** is organised into layers that ensure standardisation of data while providing flexibility of configuration. The ***acoupi application*** provides a simple
command line interface (CLI) allowing users to configure the acoupi framework for deployment. 

### Acoupi Architecture
The **acoupi** software has been designed to provide maximum flexibility and keep away the internal complexity from a user. The architecture is made of four intricate elements, which we call the data schema, components, tasks, and programs. 

The figure below provides a simplified example of an acoupi program. This program illustrates some of the most important data schema, components, and tasks.

![Figure 2: An example of a simplified acoupi program.](/docs/img/acoupi_program_simplified.png)
***Figure 2: An example of a simplified acoupi program.** This example program implements the four tasks; audio recording, model, communication and management. Each task is composed of components executing specific actions such as recording an audio file, processing it, sending results, and storing associated metadata. The components input or output data objects defined by the data schema to validate format of information flowing between compoments and tasks.*

> [!TIP]
> **Refer to the [**Developer Guide**](docs/developer_guide/index.md) section of the documentation for full details on each of these elements.**

### Acoupi Application
An acoupi application consists of the full set of code that runs at the deployment stage. This includes a set of scripts made of an acoupi program with user configurations, celery files to organise queues and workers, and bash scripts to start, stop, and reboot the application processes. An acoupi application requires the acoupi package and related dependencies to be installed before a user can configure and run it. The figure below gives an overview of key stages related to the installation, configuration and runtime of an acoupi application.

![Figure 3: Steps to deploy an acoupi application.](/docs/img/acoupi_installation_steps.png)
***Figure 3: An visual diagram highlighting the elements of an acoupi application.** Three main steps are involved in setting up and running an acoupi application: (1) installation, (2) configuration, and (3) deployment.*

## Features and development
**acoupi** builds on other Python packages. The list of the most important packages and their functions is summarised below. For more information about each of them, make sure to check their respective documentation. 
- [PDM](https://pdm-project.org/2.10/) to manage package dependencies. 
- [Pydantic](https://docs.pydantic.dev/dev/) for data validation. 
- [Pytest](https://docs.pytest.org/en/7.4.x/) as a testing framework.
- [Pony-ORM](https://ponyorm.org/) for databse queries. 
- [Celery](https://docs.celeryq.dev/en/stable/getting-started/introduction.html) to manage the processing of tasks. 
- [Jinja](#jinja) for text templating. 
