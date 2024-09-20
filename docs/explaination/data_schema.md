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
be created by instantiating a `Message` class.

### Response

A response object represents a single response received by the device when
sending a message. It contains information about the response, such as the date
and time when the message was sent, the status of the response (i.e. success,
failed, error, timeout), and the content of the response. A response can be
created by instantiating a `Response` class.

# Creating a new data object

Creating a new data object with Pydantic involves defining a Python class that
inherits from `pydantic.BaseModel`. This class acts as a blueprint for instances
of the data object, specifying the attributes and their types. The keys steps
and requirements for creating a new acoupi data objects are the following:

1. Define a Class that inherit from `BaseModel`.

```python
class YourDataObject(BaseModel):
    # Attributes for the class
```

2. Declare the attributes of the new data object as the class variables. Specify
   the attributes' data types using Python type hints. Optionally, set default
   values for the attributes.

```python
class YourDataObject(BaseModel):
    attribute1: float = 0.5
    attribute2: str
    attribute3: Path
```

3. **Optional**: Implement custom validaiton logic using
   [**Pydantic's validation methods**](https://docs.pydantic.dev/dev/concepts/validators/#annotated-validators)
   such as @field_validatior and @model_validator.

```python
class YourDataObject(BaseModel):
    attribute1: int = 0.5
    attribute2: str

    @field_validator("attribute1")
    def validate_attribute1(cls, value):
    """Check that attribute1 is a float between 0 and 1."""
    if value < 0 or value > 1:
            raise ValueError("attribute1 must be between 0 and 1")
        return value
```
