# Data Schema

The __data schema__ layer is the most basic layer of the acoupi framework. It is responsible for defining the relevants bits of information about the functionality of the device and the data it collects. The __data schema__ ensures that the data handled by the other layers of acoupi is validated and the flow of information between layers is consistent and easy to understand. 

??? Info
    We use the  [**Pydantic**](https://docs.pydantic.dev/dev/) library to build acoupi data objects.

## Acoupi Data Objects

**acoupi** comes with pre-built data objects. These are defined in the
[**acoupi.data**][acoupi.data] module. Below is an overview of a short
selection of them.

### Deployment

A deployment object holds all the information about a specific deployment. This includes information about the device, the location where the device is deployed, and the starting date. A deployment can be created by instantiating a **`data.Deployment`** class.

### Recording

A recording object represents a single recording made by the device. It contains information about the recording, such as the date and time when the recording was made, the duration and samplerate of the recording, and an optional path to the audio file. A recording can be created by instantiating the `data.Recording` class.

### Tag, Predicted Tag, BoundingBox, and Detection

AI bioacoustics models have different methods of handling audio files.

A **boundingbox** object represents the location of a sound event in time and frequency. It contains information about the start time and end time in seconds and the low frequency and high frequency in Hz of a sound event.

A **detection** object represents a single detection made by a model. It contains information about the specific recording the detection was made, the species that were detected using the `data.PredictedTag` class, and the score of the detection. A detection can be created by instantiating a `data.Detection` class.

A **predicted tag** object represents the label predicted by a model. It consists of a `data.Tag` object made of a key and a value, and a confidence score. 


### Messages

A message object represents a single message sent by the device. It contains
information about the message, such as the date and time when the message was
created, the type of the message, and the content of the message. A message can
be created by instantiating a `data.Message` class.

### Response

A response object represents a single response received by the device when
sending a message. It contains information about the response, such as the date
and time when the message was sent, the status of the response (i.e. success,
failed, error, timeout), and the content of the response. A response can be
created by instantiating a `data.Response` class.
