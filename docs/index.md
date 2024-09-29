# acoupi

## What is acoupi?

**acoupi** is an open-source Python package that streamlines bioacoustic classifier deployment on edge devices like the Raspberry Pi.
It integrates and standardizes the entire bioacoustic monitoring workflow, from recording to classification.
With various components and templates, **acoupi** simplifies the creation of custom sensors, handling audio recordings, processing, classifications, detections, communication, and data management.

<figure markdown="span">
    ![Figure 1: Overview of where the acoupi software package fits in the toolbox of bioacoustics research](img/acoupi_software_overview.jpeg){ width="50%" }
    <figcaption><b>An overview of acoupi software.</b> Input your recording settings and deep learning model of choice, and acoupi handles the rest, sending detections where you need them.
</figure>

## Requirements

Acoupi has been designed to run on single-board computer devices like the [Raspberry Pi](https://www.raspberrypi.org/) (RPi).
Users should be able to download and test acoupi software on any Linux-based machines with Python version >=3.8,<3.12 installed.

- A Linux-based single board computer such as the Raspberry Pi 4B.
- A SD Card with 64-bit Lite OS version installed.
- A USB Microphone such as an [AudioMoth USB Microphone](https://www.openacousticdevices.info/audiomoth) or an Ultramic 192K/250K.

??? tip "Recommended Hardware"

    The software has been extensively developed and tested with the RPi 4B.
    We advise users to select the RPi 4B or a device featuring similar specifications.

## Installation

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

    To check what are the available commands for acoupi, enter `acoupi --help`. Also look at the [CLI documentation](reference/cli.md) for further info.

## Ready to use AI Bioacoustics Classifiers 🚀

`acoupi` simplifies the use and implementation of open-source AI bioacoustics models.
Currently, it supports two classifiers: BatDetect2, developed by [@macodha and al.](https://doi.org/10.1101/2022.12.14.520490), and BirdNET-Lite, developed by [@kahst and al.](https://github.com/kahst).

??? warning "Licenses and Usage"

    Before using a pre-trained AI bioacoustic classifier, review its license to ensure it aligns with your intended use.
    `acoupi` programs built with these models inherit the corresponding model licenses.
    For further licensing details, refer to the [FAQ](faq.md#licensing) section.

??? warning "Model Output Reliability"

    Please note that `acoupi` is not responsible for the accuracy or reliability of model predictions.
    It is crucial to understand the performance and limitations of each model before using it in your project.

### BatDetect2 🦇

The BatDetect2 bioacoustics DL model has been trained to detect and classify UK bats species.
The [**acoupi_batdetect2**](https://github.com/acoupi/acoupi_batdetect2) repository provides users with a pre-built acoupi program that can be configured and tailored to their use cases.

The program can directly be installed with the following command:

```
pip install acoupi_batdetect2
```

And to set up and configure the `acoupi_batdetect2` program, run the command:

```{bash}
acoupi setup --program acoupi_batdetect2.program
```

### BirdNET-Lite 🦜

The BirdNET-Lite bioacoustics DL model has been trained to detect and classify a large number of bird species.
The [**acoupi_birdnet**](https://github.com/acoupi/acoupi_birdnet) repository provides users with a pre-build acoupi program that can be configured and tailored to their use cases of birds monitoring.

To install the `acoupi_birdnet` program run:

```{bash}
pip install acoupi_birdnet
```

And to setup and configure it run:

```
acoupi setup --program acoupi_birdnet.program
```

## Next steps 📖

Get to know acoupi better by exploring this documentation.

<table>
    <tr>
        <td>
            <a href="tutorials">Tutorials</a>
            <p>Step-by-step information on how to install, configure and deploy acoupi for new users.</p>
        </td>
        <td>
            <a href="how_to_guide">How-to Guides</a>
            <p>Guides to learn how to customise and built key elements of acoupi.</p>
        </td>
    </tr>
    <tr>
        <td>
            <a href="explanation">Explanation</a>
            <p>Overview of the key elements of acoupi: what they are and how they work.</p>
        </td>
        <td>
            <a href="reference">Reference</a>
            <p>Technical information refering to acoupi code.</p>
        </td>
    </tr>
</table>

!!! tip "Important"

    We would love to hear your feedback about the documentation. We are always looking to hearing suggestions to improve readability and user's ease of navigation. Don't hesitate to reach out if you have comments!

*[CLI]: Command Line Interface
*[DL]: Deep Learning
*[RPi]: Raspberry Pi
