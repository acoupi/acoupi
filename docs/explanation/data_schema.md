# Data (acoupi framework)

The **data layer** is the most basic layer of the _acoupi_ framework.
It is responsible for defining the relevant bits of information about the functionality of the device and the information it collects.
`acoupi` uses [Python's type hinting](https://docs.python.org/3/library/typing.html) extensively to clearly indicate the kinds of objects handled and produced by different parts of the system.
The **data layer** ensures that the data handled by the other layers of _acoupi_ is validated and the flow of information between layers is consistent and easy to understand.

## Why is the Data Layer Important?

Understanding the data layer is crucial when you're customising _acoupi_ components or building your own tasks.
It provides a clear and consistent structure for the information flowing through your program.

Think of it like this: the data layer defines the "language" that different parts of your _acoupi_ program use to communicate.
By using specific data objects with defined types, you ensure that everyone is on the same page.

For example, consider the definition of a `Model` in _acoupi_:

```python
from acoupi import data

class Model:
    def run(self, recording: data.Recording) -> data.ModelOutput:
        ...
```

This tells us that a `Model` in _acoupi_ takes a `Recording` object as input and produces a `ModelOutput` object.
The data layer defines exactly what information these objects contain and how they're structured.
This makes development much easier because:

- **You know what to expect:** You can rely on the data objects having specific attributes and types.
- **Code completion helps:** Your code editor can assist you by autocompleting data fields and catching potential errors.
- **Collaboration is smoother:** Everyone working with _acoupi_ understands the shared data structure.

## _acoupi_ Data Objects

_acoupi_ comes with pre-built data objects.
These are defined in the [`acoupi.data`][acoupi.data] module.
Below is an overview of a short selection of them.

### Deployment

A deployment object holds all the information about a specific deployment.
This includes information about the device, the location where the device is deployed, and the starting date.
A deployment can be created by instantiating a [**`data.Deployment`**][acoupi.data.Deployment] class.

### Recording

A recording object represents a single recording made by the device.
It contains information about the recording, such as the date and time when the recording was made, the duration and samplerate of the recording, and an optional path to the audio file.
A recording can be created by instantiating the [**`data.Recording`**][acoupi.data.Recording] class.

### Tag, Predicted Tag, BoundingBox, and Detection

AI bioacoustics models have different methods of handling audio files.

A **bounding box** object represents the location of a sound event in time and frequency.
It contains information about the start time and end time in seconds and the low frequency and high frequency in Hz of a sound event.

A **detection** object represents a single detection made by a model.
It contains information about the specific recording the detection was made, the species that were detected using the [**`data.PredictedTag`**][acoupi.data.PredictedTag] class, and the score of the detection.
A detection can be created by instantiating a [**`data.Detection`**][acoupi.data.Detection] class.

A **predicted tag** object represents the label predicted by a model.
It consists of a [**`data.Tag`**][acoupi.data.Tag] object made of a key and a value, and a confidence score.

### Messages

A message object represents a single message sent by the device.
It contains information about the message, such as the date and time when the message was created, the type of the message, and the content of the message.
A message can be created by instantiating a [**`data.Message`**][acoupi.data.Message] class.

### Response

A response object represents a single response received by the device when sending a message.
It contains information about the response, such as the date and time when the message was sent, the status of the response (i.e. success, failed, error, timeout), and the content of the response.
A response can be created by instantiating a [**`data.Response`**][acoupi.data.Response] class.

??? Info "Leveraging Pydantic for defining data schemas"

    We use the [**Pydantic**](https://docs.pydantic.dev/dev/) library to build acoupi data objects.
