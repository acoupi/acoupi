# Installation
Acoupi software has been designed to run on single-board computer devices like the Raspberry Pi. It is however possible to install and run acoupi from a laptop. The software is installable similarly than most Python packages using the preferred installer program (pip). 


## Installation Requirements
We recommend the following hardware elements to install and run acoupi. 

- single-board computer (RPi 4B or a board with similar specifications)
- 32GB microSD card (minimum) 
- USB Microphone (i.e., AudioMoth, Dodotronic Ultrasonic Mic., USB Lapel/Lavalier)

## Installation Steps
To install and use the bare-bone framework of acoupi on your embedded device follow these steps: 

**Step 1:** Install acoupi and its dependencies
```bash
pip install acoupi
```
**Step 2:** Configure acoupi default program. 
*Note: (Acoupi default program only records and saves audio files based on the settings of a user).* 
```bash
acoupi setup --program acoupi.programs.custom.acoupi
```
> ![IMPORTANT]
Please refer to the page [/user_guide/configurations](configurations.md) for an overview of the default and available configuration options when setting up the custom acoupi program.

**Step 3:** To start acoupi run the command: 
```bash
acoupi start
```
> ![IMPORTANT]
Please refer to the page [/user_guide/cli](cli.md) for an overview of the commands lines options available to manage acoupi package. 

## Other acoupi installation
Sometimes the programs might have some additional or different installation requirements. Please refer to the following links, if you wish to implement one of the pre-built bioacoustics classifiers model. 

- [acoupi-batdetect2](https://github.com/acoupi/acoupi_batdetect2) (Classifiers for UK bats species)
- [acoupi-birdnet](https://github.com/acoupi/acoupi_birdnet) (Classifiers for bird species)





