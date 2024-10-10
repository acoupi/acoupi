
# Frequently asked questions

## Technical 

### What is acoupi? 
Acoupi is an **open-source Python toolkit** that's designed to make it easy to create bioacoustic sensors on edge devices like the Raspberry Pi. Acoupi integrates and standardises the entire workflow of bioacoustic monitoring, combining both autonomous recording and classification units. Acoupi ensures **standardisation** of data while providing **flexibility of configuration** by defining attributes with specific characteristics, the *data schema* and establishing a set of methods showcasing several behaviours, the *components*. When configuring acoupi, users configure the set of acoupi components that suit their use case. 

### What isn't acoupi?
While _acoupi_ provides modular components to build your own autonomous recording and classification units, it is not a tool for training bioacoustic AI classifiers. Acoupi integrates already trained and well-tested AI bioacoustics models through its pre-built programs that you can use to perform on-device bioacoustics classification. 

### Why acoupi? 
Passive acoustic monitoring (PAM) has emerged as a practical and helpful tool for biodiversity monitoring and conservation. Combining PAM with on-device domain-specific deep-learning bioacoustics classifiers provides opportunities for extending the scale and length of data collection while alleviating downstream data storage and processing burdens. However, deploying and adapting existing solutions for its own use still requires substantial technical expertise. 

_acoupi_ aims to provide an all-in-one Python toolkit to make it easy to create your smart bioacoustic sensors on edge devices like the Raspberry Pi. With _acoupi_, you can either use one of the provided programs or build your custom program using the various tools and components that are included.

### What are the available acoupi programs? 

- __default__: The _acoupi default_ program is the most simplest program, handling only two tasks: recording and managing audio files.

- __connected__: The _acoupi connected_ program extends the default program by adding messaging capabilities, allowing users to send messages to a remote server.

- **acoupi_batdetect2**: 

- **acoupi_birdnet**:

## Usage

### For who is acoupi? 
_acoupi_ is particularly well-suited for researchers in the field of bioacoustics, but it's also a great option for environmental consultants who are looking to set up their own bioacoustic monitoring systems. 

### Is acoupi free?
Yes, acoupi is free and is licensed under the [GNU GPL-3.0](license.md). This means that acoupi will always be free to use, and free to customise for your own purpose. Please do check the license for more detailed information. 

### I want to use acoupi, but ...
- **I don't know Python.** No problem. While acoupi is built in Python, it includes a variety of pre-built programs that you can use right out of the box. Follow the [__Tutorials Section__](tutorials/index.md) to get started.

- **I don't have access to WiFi.** Acoupi does not require access to WiFi or any other wireless network. You can use acoupi as a standalone device, the audio recordings and audio classification results will be saved on the device's internal storage (i.e., the SD card). 

## Licensing
...

## Contributing

### Does acoupi accept outside contributions? 
Yes absolutely, we welcome all contributions: bug reports, bug fixes, documentation improvements, and feature requests.  

### I want to contribute. Where do I start?
Amazing! We are always looking for contributors. Make sure to read the contribution guidelines and code of conduct to get started.
