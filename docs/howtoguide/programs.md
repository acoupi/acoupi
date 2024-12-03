# Create a custom Program

## Introduction

While _acoupi_ offers a variety of [_pre-built programs_](../explanation/programs.md/#pre-built_programs) and community contributions, you might need to create a custom program for your specific needs.
This guide provides a comprehensive overview of how to create a custom program using the _acoupi_ framework.

Here's what we'll cover:

1. **Building a Program**: You'll learn the essential steps involved in creating a custom program.
2. **Tools for Program Creation**: Discover the tools and features _acoupi_ provides to simplify the development process.

!!! Tip "Before diving in!"

    This section is aimed at individuals interested in developing their own program. Make sure you have read the sections of the [Explanation](../explanation/index.md) of the documentation before going through this technical how-to guide. 

## Understanding _acoupi_ Programs

An _acoupi_ program is of a set of instructions that dictate how a smart bioacoustic sensor behaves.
It defines the tasks the sensor performs, how those tasks are configured, and the underlying execution environment.

To define an _acoupi_ program, you need to specify three key elements:

- **Tasks**: The individual units of work carried out by your program. 
- **Configuration Schema**: A "blueprint" establishing the parameters and options that users can configured to adjust the program behaviour.
- **Worker Configuration**: The lower-level settings defining how to orchestrate the tasks and runs the program on a device. 

To represent these program elements in code, _acoupi_ defines a Python class called `AcoupiProgram` ([`acoupi.programs.AcoupiProgram`][acoupi.programs.AcoupiProgram]).
This class encapsulates all the necessary information for _acoupi_ to execute a program on a device.

## Building a Program

To create a custom program in _acoupi_, you'll define a new Python class that inherits from the `AcoupiProgram` class.
This new class will encapsulate the tasks, configuration schema, and worker configuration for your program.

Here's a basic example of a custom program:

```python
from acoupi.programs import AcoupiProgram, DEFAULT_WORKER_CONFIG
from pydantic import BaseModel

class MyProgramConfig(BaseModel):
    name: str = "acoupi"  # Define a configuration option named 'name'

class MyCustomProgram(AcoupiProgram):
    worker_config = DEFAULT_WORKER_CONFIG  # Use the default worker config
    config_schema = MyProgramConfig  # Specify the configuration schema

    def setup(self, config):  # Define the program's tasks
        def my_custom_task():
            print(f"Hello {config.name}!")  # Access config values within tasks

        self.add_task(my_custom_task, schedule=60)  # Add a task that runs every 60 seconds
```

Let's break down the key elements:

### Inherit from the Base Class

```python
class MyCustomProgram(AcoupiProgram):
    ...
```

This line indicates that `MyCustomProgram` is a specialised type of `AcoupiProgram`, inheriting its core functionality and structure.
This is essential for _acoupi_ to recognise and execute your custom program.

### Create a Configuration Schema

```python
class MyProgramConfig(BaseModel):
    name: str = "acoupi"
```

We use Pydantic's `BaseModel` to define the configuration schema.
This schema specifies the options users can adjust to customise the program's behaviour.
In this example, the schema includes a single field called `name` (of type `str`) with a default value of "acoupi".
Pydantic offers valuable features like data validation and type hints, ensuring that configuration values are valid and match the expected types.

To link your configuration schema to your custom program, you'll need to define the `config_schema` attribute within your `AcoupiProgram` subclass.
This tells _acoupi_ which schema to use when validating and processing configuration values for your program.

```python
class MyCustomProgram(AcoupiProgram):
    ...

    config_schema = MyProgramConfig  # <- This indicates that this is the configuration schema for this program
```

### Provide a Worker Configuration

```python
...
from acoupi.programs import DEFAULT_WORKER_CONFIG
...

class MyProgramConfig(AcoupiProgram):
    ...
    worker_config = DEFAULT_WORKER_CONFIG
    ...
```

This line sets the `worker_config` attribute to `DEFAULT_WORKER_CONFIG`, utilising the standard worker configuration provided by _acoupi_.
The worker configuration handles lower-level aspects of program execution, which we'll keep at their default settings for now.

### Define Tasks

The core of your _acoupi_ program lies in its tasks – the individual units of work that define the sensor's behaviour.
You define these tasks within the setup method of your `AcoupiProgram` subclass.

```python
    ...

    def setup(self, config):
        def my_custom_task():
            print(f"Hello {config.name}!")

        self.add_task(
            my_custom_task,
            schedule=10
        )
```

The `setup` method is where you define the tasks your program performs.
It receives the program's configuration (`config`) as an argument, allowing tasks to access and utilise those settings.

In this example, we define a function called `my_custom_task`.
This function encapsulates the logic for a single task.
Here, it simply prints a greeting using the `name` value from the program's configuration.

[`self.add_task(...)`][acoupi.programs.AcoupiProgram.add_task] is the method that registers your task with the program.
It takes two key arguments: The first argument is the function that defines the task's logic (e.g., `my_custom_task`).
The second argument, schedule, determines how the task is executed.
In this case, `schedule=60` instructs _acoupi_ to run this task every 60 seconds.

#### Scheduling Options

_acoupi_ provides flexible options for scheduling tasks:

- **Intervals**:

Specify a number (in seconds) to run the task at regular intervals.
For more fine-grained control over intervals, use `datetime.timedelta` objects:

```python
import datetime

...

    def setup(self, config):
        ...

        self.add_task(
            my_custom_task,
            schedule=datetime.timedelta(minutes=34, seconds=15),  # Run every 34 minutes and 15 seconds
        )
```

- **Cron Expressions**

If you're familiar with cron jobs, you can use cron syntax for more complex scheduling:

```python
from celery.schedules import crontab

...

    def setup(self, config):
        ...

        self.add_task(
            my_custom_task,
            schedule=crontab(hour=7, minute=30, day_of_week=1),  # Run every Monday at 7:30 AM
        )
```

#### Task dependencies

Often, tasks within a program need to execute in a specific order or depend on the output of other tasks.
_acoupi_ enables this through callbacks.

Callbacks are functions that are executed immediately after a task completes.
The output of the preceding task is passed as an argument to the callback function.

```python
import random

...

def setup(self, config):

    ...

    def task1():
        random_number = random.randint(0, 6)
        return random_number

    def task2(number):
        if number == 6:
            print("you are lucky!")

        print("No luck yet.")

    self.add_task(
        task1,
        schedule=60,
        callbacks=[task2]
    )

    ...
```

In this example, `task2` acts as a callback for `task1`.
It receives the random number generated by `task1` and prints a message accordingly.
This ensures that `task2` always runs after `task1` and has access to its output.

This provides a basic framework for building an _acoupi_ program.
In the following sections, we'll explore more advanced concepts and tools to enhance your custom programs.

## Tools for Program Creation

Now that you understand the fundamentals of program creation, let's explore the tools _acoupi_ provides to facilitate your development process and help you to build meaningful bioacoustic monitoring solutions.

_acoupi_ offers several approaches to simplify and accelerate the creation of custom programs:

- **Program Templates**: Leverage pre-defined templates with commonly used tasks and components to expedite development.
- **Predefined Configuration Schemas**: Utilise existing schemas for typical program components, saving time and effort in defining configuration options.
- **Task Templates**: Employ templates for frequently used tasks, such as recording audio or sending data, as building blocks for your program.
- **Component Selection**: Modify existing tasks by replacing default components with alternatives or custom implementations to tailor functionality.

Now we will explore each of these methods, giving insight into how to create custom programs within the _acoupi_ framework.

### Program Templates

When building a program, you often need to incorporate basic functionality, such as audio recording and management.
_acoupi_ provides program templates that serve as foundational building blocks, saving you time and effort.

#### Basic Program

The [`BasicProgram`][acoupi.programs.templates.BasicProgram] provides a convenient starting point for programs that require fundamental audio recording and management capabilities.
By incorporating this template, you can quickly set up a program that captures audio data and organises recordings efficiently.

To use the `BasicProgram`, define your custom program class that inherits from it:

```python
from acoupi.programs.templates import BasicProgram, BasicProgramConfiguration

class CustomProgram(BasicProgram):

    config_schema = BasicProgramConfiguration
```

This automatically equips your `CustomProgram` with two essential tasks:

- **Recording Task**: This task handles the core audio recording functionality.
    It checks recording conditions, captures audio segments of a defined duration at specified intervals, and temporarily stores the recordings.
    This task utilises the `generate_recording_task` template ([`acoupi.tasks.generate_recording_task`][acoupi.tasks.generate_recording_task]) for its implementation.

- **File Management Task**: This task manages the recorded audio files.
    It processes the temporary recordings, determining which recordings to save permanently based on predefined criteria (by default, all recordings are saved).
    Saved recordings are organised in a structured folder hierarchy: `<base_directory>/<year>/<month>/<day>/<time>_<recording_id>.wav`.
    This task is based on the `generate_file_management_task` template ([`acoupi.tasks.generate_file_management_task`][acoupi.tasks.generate_file_management_task]).

The `BasicProgram` uses the `BasicProgramConfiguration` schema ([`acoupi.programs.templates.BasicProgramConfiguration`][acoupi.programs.templates.BasicProgramConfiguration]) to define its configurable parameters.
To extend these parameters, you can create a new configuration class that inherits from `BasicConfiguration` and adds your custom fields:

```python
class ExpandedConfigurations(BasicConfiguration):
    other_field: bool = True
    # ... your additional fields ...
```

While the `BasicProgram` provides a solid foundation, you can further customise its behaviour by overriding specific methods.
For instance, you can modify the recording conditions to control when audio recording occurs:

```python
from acoupi.components.types import RecordingCondition

class IsWarmEnough(RecordingCondition):
    def __init__(self, threshold):
        self.threshold = threshold

    def should_record(self):
        # This is a hypothetical sensor, not included in acoupi
        temperature = sensor.get_current_temperature()
        return temperature >= self.threshold

class CustomProgram(BasicProgram):
    # ... other parts of your program ...

    def get_recording_conditions(self, config):
        # Get the default conditions (e.g., recording interval)
        default_conditions = super().get_recording_conditions(config)
        return [
            *default_conditions,
            IsWarmEnough(config.temperature_threshold)  # Add your custom condition
        ]
```

For a complete understanding of the `BasicProgram`'s capabilities and customisation options, refer to its [reference documentation][acoupi.programs.templates.BasicProgram].

#### Messaging Program

The [`MessagingProgram`][acoupi.programs.templates.MessagingProgram] extends the `BasicProgram` to add messaging capabilities.
This allows your programs to send messages and heartbeats to remote servers via HTTP or MQTT.

To incorporate messaging functionality into your program, define your custom program class that inherits from `MessagingProgram`:

```python
from acoupi.programs.templates import MessagingProgram, MessagingProgramConfig

class CustomConfig(MessagingProgramConfig):
    # ... your custom configuration fields ...

class CustomProgram(MessagingProgram):

    config_schema = CustomConfig
```

This equips your program with the following messaging features:

- **Messenger**: A [`Messenger`][acoupi.components.types.Messenger] object is created, allowing you to choose between HTTP or MQTT protocols for message delivery.
- **Message Store**: A dedicated message store is initialised to keep track of all messages generated by your device, including their delivery status.
- **Send Messages Task**: This periodic task (running every 2 minutes by default, but configurable) checks the message store for pending messages and attempts to deliver them.
    It leverages the [`generate_send_messages_task`][acoupi.tasks.generate_send_messages_task] template for its implementation.
- **Heartbeat Task**: This task periodically sends a heartbeat message (every 30 minutes by default, configurable) containing information about the device's status, ID, and the current time.
    This provides a regular indication that the device is active and functioning correctly.

By default, the `MessagingProgram` doesn't generate any messages on its own.
Its primary purpose is to provide the underlying framework for sending messages.
You can easily create and send messages from your custom tasks using the `message_store`:

```python
from acoupi.data import Message
import datetime

class CustomProgram(MessagingProgram):

    def setup(self, config):
        super().setup(config)  # Initialise the messaging components

        def random_task():
            current_time = datetime.datetime.now()
            message = Message(content=f"Hi! The current time is {current_time}")
            self.message_store.store_message(message)  # Add the message to the store

        self.add_task(  # Register the task in your program
            random_task,
            schedule=3600 # Every hour
        )

        # ... your other tasks ...
```

In this example, `random_task` creates a simple message and stores it in the `message_store`.
The **Send Messages Task** will then handle delivering this message at its next scheduled execution.

For detailed information about the configuration options and customisation possibilities of the `MessagingProgram`, consult its comprehensive [reference documentation][acoupi.programs.templates.MessagingProgram].

#### Detection Program

To create an Acoupi program that performs audio detection and sends detection information to a remote server, you can use the [`DetectionProgram`][acoupi.programs.templates.DetectionProgram] template.
This template builds upon the `BasicProgram` and `MessagingProgram` templates, inheriting their functionality for audio recording, file management, heartbeats, and sending messages.

The `DetectionProgram` adds a detection task that runs a detection model on recorded audio segments.
This allows you to create "smart" bioacoustic detectors that can automatically identify sounds or events of interest.

To use the `DetectionProgram` template, define your custom program class that inherits from `DetectionProgram` and implement the `configure_model` method:

```python
from acoupi.programs.templates import DetectionProgram, DetectionProgramConfig
from acoupi_birdnet.models import BirdNET



class CustomConfig(DetectionProgramConfig):
    threshold: float = 0.5
    # ... your custom fields ...

class CustomProgram(DetectionProgram):

    config_schema = CustomConfig

    #
    def configure_model(self, config):
        # create a model instance with your configurations
        return BirdNET(threshold=config.threshold)
```

The `configure_model` method should return any component that inherits from the [types.Model][acoupi.components.types.Model] class.
This allows you to use any compatible detection model with your program.

By defining a program like this, it will automatically create a new task called "detection_task" that will be triggered whenever a recording has been successfully finalised.

The `DetectionProgram` template offers several customisation options:

- `get_message_factories`: Override this method to customise the messages generated based on the detection results.
    For example, you can create messages that are sent whenever a particular species is detected or when there is a high level of acoustic diversity.

```python
from acoupi.components import DetectionThresholdMessageBuilder

class CustomProgram(DetectionProgram):
    ...

    def get_message_factories(self, config):
        return [
            # This message factory will remove any detections below 0.8 score
            # but otherwise will send everything
            DetectionThresholdMessageBuilder(threshold=0.8)
        ]
```

- `get_output_cleaners`: Override this method to define a list of output cleaners that will be applied to the model's raw output to clean it up or extract relevant information.
    By default, a single cleaner is included: a threshold cleaner.
    This cleaner removes all detections with a confidence score below a specified threshold.
    This threshold is configurable via the detections.
    threshold field in your DetectionProgramConfiguration, enabling you to fine-tune the sensitivity of your detection program at deployment time.
    You can override this method to add or customize output cleaners according to your specific needs.

- `get_processing_filters`: Override this method to define a list of processing filters that will be applied to each recording before it is processed by the model.
    These filters determine whether a recording should be processed at all.
    This can be useful to avoid unnecessary model processing when it is not required by the context or based on simple heuristics on the recording content.

For more info on how this program can be configured have a look at its [reference documentation][acoupi.programs.templates.DetectionProgram].

### Predefined Configuration Schemas

Defining a clear configuration schema is important when designing effective and adaptable _acoupi_ programs.
A well-structured schema promotes program flexibility, provides clear guidance to users on configurable options, and ensures that configurations are validated before deployment, preventing potential issues.

While you'll need to create custom schemas for program-specific behaviours, _acoupi_ strongly encourages reusing predefined schemas for common components.
This approach not only saves you time and effort but also ensures compatibility with program templates and benefits from carefully designed and validated schema structures.

_acoupi_ provides a collection of predefined schemas for common components:

1. [**MicrophoneConfig**][acoupi.components.MicrophoneConfig]: This schema facilitates configuration of the microphone device, including device selection, sampling rate, and the number of channels.
      It's highly customised for ease of use during setup, so utilising it is recommended for streamlined microphone configuration.

2. [**MQTTConfig**][acoupi.components.MQTTConfig] and [**HTTPConfig**][acoupi.components.HTTPConfig]: These schemas streamline the configuration of MQTT and HTTP messengers, respectively, for programs that require communication capabilities.

3. [**PathsConfiguration**][acoupi.programs.templates.PathsConfiguration]: This schema defines options for configuring storage locations for audio recordings and metadata.
      By default, temporary recordings are stored in memory (if available) and permanent recordings are saved in `$HOME/audio/`, but you can customise these paths according to your needs.

4. [**RecordingConfiguration**][acoupi.programs.templates.AudioConfiguration]: This schema covers the essential parameters for the recording task, such as recording duration, recording interval, and scheduling options.

5. [**MessagingConfiguration**][acoupi.programs.templates.MessagingConfig]: This schema encompasses all the necessary settings for configuring the messaging task.

These predefined schemas are further grouped into higher-level schemas for broader functionalities:

1. [**BasicConfiguration**][acoupi.programs.templates.BasicProgramConfiguration]: This schema combines `MicrophoneConfig`, `PathsConfiguration`, and `RecordingConfiguration`, providing all the essential configurations for a basic _acoupi_ program.

2. [**MessagingProgramConfiguration**][acoupi.programs.templates.MessagingProgramConfiguration]: This schema includes the necessary configurations for using the `MessagingProgram`, enabling message sending capabilities in your programs.

Leverage these predefined schemas as building blocks to construct comprehensive configuration schemas tailored to your specific program requirements.
This modular approach promotes consistency, reduces redundancy, and ensures your programs are well-structured and easily configurable.

### Task Templates

For more granular control over your program's tasks and components, _acoupi_ offers task templates.
These templates are functions that generate pre-built tasks with customisable components, allowing you to assemble program logic efficiently while maintaining flexibility.

1. [**`generate_recording_task`**][acoupi.tasks.generate_recording_task]: This template creates a task that handles the fundamental aspects of audio recording.
      It allows you to define custom recording conditions to specify when recording should occur and automatically stores recording metadata for future reference.

2. [**`generate_file_management_task`**][acoupi.tasks.generate_file_management_task]: This template generates a task that manages temporary audio recordings.
      It ensures recordings are ready to be moved (e.g., after processing), selects which recordings to save permanently, and organises them in the designated storage location.

3. [**`generate_send_messages_task`**][acoupi.tasks.generate_send_messages_task]: This template creates a task responsible for sending pending messages to remote endpoints using the configured messengers (e.g. HTTP or MQTT).

4. [**`generate_detection_task`**][acoupi.tasks.generate_detection_task]: This template generates a task that performs audio analysis using a specified model.
      It includes preliminary checks to determine if the model should be run on a given recording, executes the model, post-processes the results, generates messages based on detections, and stores detection information in the metadata store.

5. [**`generate_heartbeat_task`**][acoupi.tasks.generate_heartbeat_task]: This template creates a task that periodically sends heartbeat messages via the configured messengers, providing status updates and ensuring the device remains connected.

6. [**`generate_summariser_task`**][acoupi.tasks.generate_summariser_task]: This template generates tasks that analyse the metadata store to produce meaningful summaries of recorded data and detections.
      These summaries are then packaged as messages for remote delivery.

Each task template requires specific components as arguments.
However, this requirement is flexible in that you need to provide components of the correct type rather than specific instances.
This allows you to integrate custom components into the pre-built task workflows.

For example, the `generate_detection_task` function requires components such as a [`Store`][acoupi.components.types.Store], [`Model`][acoupi.components.types.Model], [`MessageStore`][acoupi.components.types.MessageStore], etc.:

```python
def generate_detection_task(
    store: types.Store,
    model: types.Model,
    message_store: types.MessageStore,
    # ... other optional components ...
) -> Callable[[data.Recording], None]:
    ...
```

As long as you provide components that adhere to the specified types, the generated task will function correctly within the defined workflow.

To understand the specific requirements and workflows of each task template, consult their respective documentation for detailed information.
This will guide you in selecting the appropriate components and customising the tasks to suit your program's needs.

### Component Selection

_acoupi_ offers a wide array of pre-built components to streamline your program and task development.
These components cover essential functionalities such as messaging, metadata storage, file management, and more.
Refer to the reference documentation for a comprehensive [list of available components][acoupi.components].

You can readily swap these pre-built components within default implementations or when creating custom tasks.
As long as your chosen components adhere to the required type specifications, they should integrate seamlessly.

Beyond the built-in components, you can also leverage community-created components.
For instance, the `acoupi_batdetect2` and `acoupi_birdnet` modules provide ready-to-use `Batdetect2` and `BirdNET` models (of type [`acoupi.components.types.Model`][acoupi.components.types.Model]) for your custom programs.
If you develop your own components that you believe would benefit the _acoupi_ community, please reach out to us for guidance on sharing them.

## Conclusion

Here we covered what you need to get started for building your custom program.
Dive into the reference documentation to see the details of the individual parts that were covered here.
If you have a question, it might already be covered by our [FAQ](../faq.md), but you can also reach out through our [GitHub](https://github.com/acoupi/acoupi) repository.
