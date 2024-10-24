# Frequently asked questions

## Technical

### What is _acoupi_?

_acoupi_ is an **open-source Python toolkit** that's designed to make it easy to create bioacoustic sensors on edge devices like the Raspberry Pi.
_acoupi_ integrates and standardises the entire workflow of bioacoustic monitoring, combining both autonomous recording and classification units.
_acoupi_ ensures **standardisation** of data while providing **flexibility of configuration** by defining attributes with specific characteristics, the _data schema_ and establishing a set of methods showcasing several behaviours, the _components_.
When configuring _acoupi_, users configure the set of _acoupi_ components that suit their use case.

### What _acoupi_ isn't?

While _acoupi_ provides modular components to build your own autonomous recording and classification units, it is not a tool for training bioacoustic AI classifiers.
_acoupi_ integrates already trained and well-tested AI bioacoustic models through its pre-built programs that you can use to perform on-device bioacoustic classification.

### Why _acoupi_?

Passive acoustic monitoring (PAM) has emerged as a practical and helpful tool for biodiversity monitoring and conservation.
Combining PAM with on-device domain-specific deep-learning bioacoustic classifiers provides opportunities for extending the scale and length of data collection while alleviating downstream data storage and processing burdens.
However, deploying and adapting existing solutions for its own use still requires substantial technical expertise.

_acoupi_ aims to provide an all-in-one Python toolkit to make it easy to create your smart bioacoustic sensors on edge devices like the Raspberry Pi.
With _acoupi_, you can either use one of the provided programs or build your custom program using the various tools and components that are included.

### What are the available _acoupi_ programs?

- **default**: The _acoupi default_ program is the most simplest program, handling only two tasks: recording and managing audio files.

- **connected**: The _acoupi connected_ program extends the default program by adding messaging capabilities, allowing users to send messages to a remote server.

- **acoupi_batdetect2**:

- **acoupi_birdnet**:

## Usage

### Who can use _acoupi_?

_acoupi_ is particularly well-suited for researchers in the field of bioacoustics, but it's also a great option for environmental consultants who are looking to set up their own bioacoustic monitoring systems.

### Is _acoupi_ free?

Yes, _acoupi_ is free and is licensed under the [GNU GPL-3.0](license.md).
This means that _acoupi_ will always be free to use, and free to customise for your own purpose.
Please do check the license for more detailed information.

### I want to use _acoupi_, but ...

- **I don't know Python.** No problem.
    While _acoupi_ is built in Python, it includes a variety of pre-built programs that you can use right out of the box.
    Follow the [**Tutorials Section**](tutorials/index.md) to get started.

- **I don't have access to WiFi.** _acoupi_ does not require access to WiFi or any other wireless network.
    You can use _acoupi_ as a standalone device, the audio recordings and audio classification results will be saved on the device's internal storage (i.e., the SD card).

## Licensing

### Can I use _acoupi_ for commercial purposes?

Yes, absolutely! _acoupi_ is licensed under the [GNU GPL-3.0](license.md), which explicitly permits commercial use.
However, the GPL-3.0 is a "copyleft" license.
This means that if you modify _acoupi_ or create a new work based on it (whether for commercial or non-commercial purposes), you must make your derived work available under the same GPL-3.0 license.
Essentially, this requires you to keep your source code open and freely available.

### Does the license apply to the recordings produced by _acoupi_?

No, the GPL-3.0 license doesn't apply to the audio recordings themselves.
Copyright law governs those.
You own the copyright to any recordings you make using _acoupi_ and are free to use them as you wish.

### Does the license apply to the detections produced by _acoupi_?

This is a bit more nuanced.
_acoupi_ itself doesn't provide detection models; it provides the framework for running them.
The license of the detection model you use will determine how you can use the detections.
If you use a pre-trained model, carefully check its license.
Some models may be open source, allowing free use of the detections.
Others may have restrictions, especially for commercial use.
It's always best to consult with a legal professional for specific advice on licensing and copyright matters, especially when commercial use is involved.

## Contributing

### Does _acoupi_ accept outside contributions?

Yes absolutely, we welcome all contributions: bug reports, bug fixes, documentation improvements, and feature requests.

### I want to contribute. Where do I start?

Amazing! We are always looking for contributors.
Make sure to read the contribution guidelines and code of conduct to get started.
