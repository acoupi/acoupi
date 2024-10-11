# Installation

_acoupi_ has been designed to run on single-board computer devices like the [Raspberry Pi](https://www.raspberrypi.org/) (RPi).
Users should be able to download and test _acoupi_ software on any Linux-based machine with Python version >=3.8,<3.12 installed.

## Installation Requirements

We recommend the following hardware elements to install and run _acoupi_.

- A Linux-based single board computer such as the Raspberry Pi 4B.
- A SD Card with 64-bit Lite OS version installed.
- A USB Microphone such as an [AudioMoth USB Microphone](https://www.openacousticdevices.info/audiomoth) or an Ultramic 192K/250K.

??? tip "Recommended Hardware"

    The software has been extensively developed and tested with the RPi 4B.
    We advise users to select the RPi 4B or a device featuring similar specifications.

## Installation Steps

??? tip "Getting started with Raspberry Pi"

    If you are new to RPi, we recommend you reading and following the RPi's [**Getting started**](https://www.raspberrypi.com/documentation/computers/getting-started.html) documentation.

To install and use the bare-bone framework of _acoupi_ on your embedded device follow these steps:

**Step 1:** Install _acoupi_ and its dependencies

!!! Example "CLI Command: install acoupi"

    ```bash
    curl -sSL https://github.com/acoupi/acoupi/raw/main/scripts/setup.sh | bash
    ```

**Step 2:** Configure an _acoupi_ program.

_acoupi_ includes a default program for recording and saving audio files based on your settings, similar to an AudioMoth setup.
To start using it, enter the command:

!!! Example "CLI Command: setup _acoupi default_ program"

    ```bash
    acoupi setup --program acoupi.programs.default
    ```

**Step 3:** To start a deployment of _acoupi_ with the configured program run the command:

!!! Example "CLI Command: start a configured _acoupi_ program"

    ```bash
    acoupi deployment start
    ```

??? tip "Using _acoupi_ from the command line"

    To check what are the available commands for _acoupi_, enter `acoupi --help`. Also look at the [CLI documentation](../reference/cli.md) for further info.
