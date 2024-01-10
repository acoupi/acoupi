
# Frequently asked questions

## Technical 

### What is acoupi? 
**Acoupi** is an open-source Python toolkit that's designed to make it easy to create bioacoustic sensors on edge devices like the Raspberry Pi. **Acoupi** has flexibility at its core. **Acoupi** integrates and standardises the entire workflow of bioacoustic monitoring, combining both autonomous recording and classification units. **Acoupi** includes individual components for audio recordings, audio processing, audio classifications and detections, results communication, and audio files and results management. 

### What isn't acoupi?
While **acoupi** provides modular components to build your own autonomous recording and classification units, it is not a tool for training bioacoustic AI classifiers. **Acoupi** integrates already trained and well-tested AI bioacoustics models through its pre-built programs that you can use to perform on-device bioacoustics classification. 

### Why acoupi? 
Passive acoustic monitoring (PAM) has emerged as a practical and helpful tool for biodiversity monitoring and conservation. Combining PAM with on-device domain-specific deep-learning bioacoustics classifiers provides opportunities for extending the scale and length of data collection while alleviating downstream data storage and processing burdens. However, deploying and adapting existing solutions for its use still requires substantial technical expertise. 

**Acoupi** aims to provide an all-in-one Python toolkit to make it easy to create your smart bioacoustic sensors on edge devices like the Raspberry Pi. With **Acoupi**, you can either use one of the provided programs or build your custom program using the various tools and components that are included.


### How does acoupi compare to ... 
- [**AudioMoth?**](https://www.openacousticdevices.info/audiomoth)
- **BirdNET-Pi?**
- **PUC?**

## Usage

### For who is acoupi? 
**Acoupi** is particularly well-suited for researchers in the field of bioacoustics, but it's also a great option for environmental consultants who are looking to set up their own bioacoustic monitoring systems. 

### Is acoupi free?
Yes, acoupi is free and will always be free. That means you can use acoupi freely for personal, academic, or other non-commercial applications.


### I want to use acoupi, but ...
- **I don't know Python.** No problem. While acoupi is built in Python, it includes a variety of pre-built programs that you can use right out of the box. Follow the [installation guide](#installation.md) to get started and have a look at the various pre-built [programs](#programs.md) you can use. 

- **I don't have access to WiFi.** Acoupi does not require access to WiFi or any other wireless network. You can use acoupi as a standalone device, the audio recordings and audio classification results will be saved on the device's internal storage (i.e., the SD card). 
- **I don't have my own AI classifier.** 

## Contributing

### Does acoupi accept outside contributions? 
Yes absolutely, we welcome all contributions: bug reports, bug fixes, documentation improvements, and feature requests.  

### I want to contribute. Where do I start?
But perhaps best of all, **Acoupi** is designed with ease-of-use in mind. We understand that not everyone has a background in programming or signal processing, so we've taken care to make the toolkit as user-friendly as possible. So whether you're an expert or a beginner, you'll find that **Acoupi** is a breeze to work with.
