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

![Figure 1: Overview of where the acoupi software package fits in the toolbox of bioacoustics research](/docs/img/acoupi_software_overview.png)
*Figure 1: Overview of where the acoupi software package fits in the toolbox 
of bioacoustics research.*

## Requirements
Acoupi has been designed to run on single-board computer devices like the RPi. The software has been extensively developed and tested with the RPi 4B. We advise users to select the RPi 4B or a device featuring similar specifications. 

Users should be able to download and test acoupi software on any Linux-based machines with Python version >=3.8,<3.12 installed. 

- A Linux-based single board computer such as the Raspberry Pi 4B. 
- A SD Card with 64-bit Lite OS version installed.
- A USB Microphone such as an AudioMoth, a µMoth, an Ultramic 192K/250K.

## Installation
> [!IMPORTANT]
> To install one of the acoupi pre-built programs containing either the **BatDetect2** or the **BirdNET-Lite** bioacoustics classifiers, refer to the information in the below section: [Pre-built AI bioacoustics classifiers](#pre-built-ai-bioacoustics-classifiers).

To install and use the bare-bone framework of acoupi on your embedded device follow these steps: 

**Step 1:** Install acoupi and its dependencies
```
pip install acoupi
```
**Step 2:** Configure acoupi default program. 

(*Note: acoupi comes with a test and a default program. The default program is only recording and saving audio files based on the users' settings. Think like something similar to the setup of an AudioMoth*). 
```
acoupi setup --program `program-name`
```
For acoupi  program, enter this command: 
```
acoupi setup --program acoupi.custom.acoupi
```
**Step 3:** To start acoupi run the command: 
```
acoupi start
```

> [!TIP]
> To check what are the available commands for acoupi, enter `acoupi --help`.

## Pre-built AI Bioacoustics Classifiers

With acoupi, we aim to facilitate the use and implementation of open-source AI bioacoustics models. We currently provide the configuration for two bioacoustics classifers; the [**BatDetect2**](https://github.com/macaodha/batdetect2) developed by [@macodha and al.](https://doi.org/10.1101/2022.12.14.520490) and the [**BirdNET-Lite**](https://github.com/kahst/BirdNET-Lite) developed by [@kahst and al.](https://github.com/kahst).

### BatDetect2

The BatDetect2 bioacoustics DL model has been trained to detect and classify UK bats species. The [**acoupi_batdetect2**](https://github.com/acoupi/acoupi_batdetect2) repository provides users with a pre-build acoupi program that can be configured and tailored to their use cases of UK Bats monitoring. 

The program can directly be installed and configured by typing these two commands in a CLI: 
```
pip install acoupi_batdetect2
acoupi setup --program acoupi_batdetect2.program
```

### BirdNET-Lite

The BirdNET-Lite bioacoustics DL model has been trained to detect and classify a large number of bird species. The [**acoupi_birdnet**](https://github.com/acoupi/acoupi_birdnet) repository provides users with a pre-build acoupi program that can be configured and tailored to their use cases of birds monitoring. 

The program can directly be installed and configured by typing these two commands in a CLI: 
```
pip install acoupi_birdnet
acoupi setup --program acoupi_birdnet.program
```


## Acoupi Software Architecture
Acoupi software is divided into two parts; the code base framework and the running application. The ***acoupi framework*** is organised into a layered architecture that ensures standardisation of data while providing flexibility of configuration. The ***acoupi application*** provides a simple
command line interface (CLI) allowing users to configure the acoupi framework for deployment. 

### Acoupi Framework
The **acoupi** framework has been designed to provide maximum flexibility and keep away the internal complexity from a user. The framework is made of four intricate elements, which we call the data schema, components, tasks, and programs. 

The figure below provides a simplified example of an acoupi program. This program illustrates some of the most important data schema, components, and tasks.

![Figure 2: Example of a simplified acoupi program.](/docs/img/acoupi_program_simplified.png)
*Figure 2: Example of a simplified acoupi program.*

Refer to the [**Developer Guide**](docs/developer_guide/index.md) section of the documentation for full details on each of these elements.

### Acoupi Application
An acoupi application consists of the full set of code that runs at the deployment stage. This includes a set of scripts made of an acoupi program with user configurations, celery files to organise queues and workers, and bash scripts to start, stop, and reboot the application processes. An acoupi application requires the acoupi package and related dependencies to be installed before a user can configure and run it. The figure below gives an overview of key stages related to the installation, configuration and runtime of an acoupi application.

![Figure 3: Overview of steps to follow to install, configure, and start an acoupi application.](/docs/img/acoupi_installation_steps.png)
*Figure 3: Overview of steps to follow to install, configure, and start an acoupi application.*

## Features and development
**acoupi** builds on other Python packages. The list of the most important packages and their functions is summarised below. For more information about each of them, make sure to check their respective documentation. 
- [PDM](https://pdm-project.org/2.10/) to manage package dependencies. 
- [Pydantic](https://docs.pydantic.dev/dev/) for data validation. 
- [Pytest](https://docs.pytest.org/en/7.4.x/) as a testing framework.
- [Pony-ORM](https://ponyorm.org/) for databse queries. 
- [Celery](https://docs.celeryq.dev/en/stable/getting-started/introduction.html) to manage the processing of tasks. 
- [Jinja](#jinja) for text templating. 