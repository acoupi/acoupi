# What are acoupi built-in programs?

**acoupi** comes with a set of built-in programs to get you started without any additional configuration. These programs are designed to cover a range of use cases in bioacoustics and environmental monitoring.

## acoupi

The ``acoupi`` program is the basic use case of **acoupi**. If you just want to record audio from the microphone and save it to a file, this program is for you. It's easy to configure when to start and stop recording, the interval between each recording, and the duration of each recording. With these settings, you can make **acoupi** behave like an AudioMoth.

## BatDetect2

The ``batdetect2`` program is a UK bat detector that not only records audio from the microphone but also performs real-time bat detection and classification using the BatDetect2 model. With ``batdetect2``, you can store the detections and even send them to a remote server for further processing. It's great for
researchers or environmental consultants who want to identify UK bat species in real-time.

Please refer to the GitHub Repository [`acoupi_batdetect2`](https://github.com/acoupi/acoupi_batdetect2) for more details about the ``batdetect2`` program.

## BirdNET
The ``birdnet`` program is similar to the bat detector, but it's for bird detection and classification. It uses the BirdNET-Lite model to detect and classify bird sounds in real-time. If you're interested in monitoring bird populations or studying bird behavior, this program is perfect for you.

Please refer to the GitHub Repository [`acoupi_birdnet`](https://github.com/acoupi/acoupi_birdnet) for more details about the ``birdnet`` program.

## Custom Program
Please refer to the ``developer_guide`` documentations. 