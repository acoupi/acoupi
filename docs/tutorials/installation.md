# Installation

Acoupi has been designed to run on single-board computer devices like the [Raspberry Pi](https://www.raspberrypi.org/) (RPi). Users should be able to download and test acoupi software on any Linux-based machines with Python version >=3.8,<3.12 installed.

## Installation Requirements

We recommend the following hardware elements to install and run acoupi.

- A Linux-based single board computer such as the Raspberry Pi 4B.
- A SD Card with 64-bit Lite OS version installed.
- A USB Microphone such as an [AudioMoth USB Microphone](https://www.openacousticdevices.info/audiomoth) or an Ultramic 192K/250K.

??? tip "Recommended Hardware"

    The software has been extensively developed and tested with the RPi 4B.
    We advise users to select the RPi 4B or a device featuring similar specifications.

## Installation Steps

??? tip "Getting started with Raspberry Pi"

    If you are new to RPi, we recommend you reading and following the RPi's [**Getting started**](https://www.raspberrypi.com/documentation/computers/getting-started.html) documentation. 

To install and use the bare-bone framework of acoupi on your embedded device follow these steps:

**Step 1:** Install acoupi and its dependencies

```
curl -sSL https://github.com/acoupi/acoupi/raw/main/scripts/setup.sh | bash
```

**Step 2:** Configure an acoupi program.

```
acoupi setup --program `program-name`
```

`acoupi` includes a default program for recording and saving audio files based on your settings, similar to an AudioMoth setup.
To start using it, simply enter the following command:

```
acoupi setup --program acoupi.programs.default
```

**Step 3:** To start a deployment of `acoupi` with the configured program run the command:

```
acoupi deployment start
```

??? tip "Using acoupi from the command line"

    To check what are the available commands for acoupi, enter `acoupi --help`. Also look at the [CLI documentation](user_guide/cli.md) for further info.

## Other acoupi installation

Sometimes the programs might have some additional or different installation requirements. Please refer to the following links, if you wish to implement one of the pre-built bioacoustics classifiers model.

- [acoupi-batdetect2](https://github.com/acoupi/acoupi_batdetect2) (Classifiers for UK bats species)
- [acoupi-birdnet](https://github.com/acoupi/acoupi_birdnet) (Classifiers for bird species)
