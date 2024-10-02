# Create a custom Program

## Introduction

While _acoupi_ offers a variety of pre-built programs and community contributions, you might need to create a custom program for your specific needs.
This guide provides a comprehensive overview of program creation within the _acoupi_ framework.

Here's what we'll cover:

1. **Understanding _acoupi_ Programs**: We'll explore the core concepts an _acoupi_ program.
2. **Building a Program**: You'll learn the essential steps involved in creating a custom program.
3. **Tools for Program Creation**: Discover the tools and features _acoupi_ provides to simplify the development process.

## Understanding _acoupi_ Programs

Before diving into building your own program, let's clarify what constitutes an _acoupi_ program and its fundamental components.

Essentially, an _acoupi_ program is a set of instructions that dictate how your smart bioacoustic sensor behaves.
It defines the tasks the sensor performs, how those tasks are configured, and the underlying execution environment.

To define an _acoupi_ program, you need to specify three key elements:

- **Tasks**: These are the individual units of work carried out by your program.
    Think of them as the building blocks of your sensor's behavior.
    Each task has a specific purpose, whether it's recording audio or runnning a model.
    When defining a task, you specify:

      - _Functionality_: What the task actually does.
      - _Scheduling_: When and how often the task runs (e.g., continuously, at specific intervals, triggered by an event).
      - _Dependencies_: How the task relates to other tasks in the program (e.g., does it need to run before or after another task?).

* **Configuration Schema**: This acts as a blueprint for customizing your program.
    It defines the parameters and options that users can modify to adjust the program's behavior.
    A well-defined schema ensures your program is flexible and adaptable to different needs and scenarios.

* **Worker Configuration**: This encompasses lower-level settings related to how the program runs on the device.
    For simplicity, this guide uses the default worker configuration, allowing you to focus on the core aspects of program design.

To represent these program elements in code, _acoupi_ defines a Python class called `AcoupiProgram` ([`acoupi.programs.AcoupiProgram`][acoupi.programs.AcoupiProgram]).
This class encapsulates all the necessary information for _acoupi_ to execute your program on a device.
Therefore, creating a custom program involves defining your own `AcoupiProgram` class, which we'll explore in the next section.

## Building a Program

To create a custom program in acoupi, you'll define a new Python class that inherits from the `AcoupiProgram` class.
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
This is essential for _acoupi_ to recognize and execute your custom program.

### Create a Configuration Schema

```python
class MyProgramConfig(BaseModel):
    name: str = "acoupi"
```

We use Pydantic's BaseModel to define the configuration schema.
This schema specifies the options users can adjust to customize the program's behaviour.
In this example, the schema includes a single field called name (of type str) with a default value of "acoupi".
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

This line sets the worker_config attribute to DEFAULT_WORKER_CONFIG, utilizing the standard worker configuration provided by acoupi.
The worker configuration handles lower-level aspects of program execution, which we'll keep at their default settings for now.

### Define Tasks

The core of your _acoupi_ program lies in its tasks – the individual units of work that define the sensor's behavior.
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
It receives the program's configuration (`config`) as an argument, allowing tasks to access and utilize those settings.

In this example, we define a function called `my_custom_task`.
This function encapsulates the logic for a single task.
Here, it simply prints a greeting using the `name` value from the program's configuration.

[`self.add_task(...)`][acoupi.programs.AcoupiProgram.add_task] is the method that registers your task with the program.
It takes two key arguments: The first argument is the function that defines the task's logic (e.g., `my_custom_task`).
The second argument, schedule, determines how the task is executed.
In this case, `schedule=60` instructs _acoupi_ to run this task every 60 seconds.

#### Scheduling Options

acoupi provides flexible options for scheduling tasks:

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
acoupi enables this through callbacks.

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
- **Predefined Schemas**: Utilize existing schemas for typical program components, saving time and effort in defining configuration options.
- **Task Templates**: Employ templates for frequently used tasks, such as recording audio or sending data, as building blocks for your program.
- **Component Selection**: Modify existing tasks by replacing default components with alternatives or custom implementations to tailor functionality.

Now we will explore each of these methods, giving insight into how to create custom programs within the _acoupi_ framework.

### Program Templates

When building a program, you often need to incorporate basic functionality, such as audio recording and management.
_acoupi_ provides program templates that serve as foundational building blocks, saving you time and effort.

Here are two examples of program templates:

- **BasicProgramMixin**: This template provides essential features for recording audio and managing recordings, forming a solid base for most bioacoustic monitoring programs.
- **MessagingProgramMixin**: This template adds functionality for sending messages and heartbeats to remote servers.

??? info "What is a Mixin?"

    In object-oriented programming, a mixin is a class that provides a specific set of functionalities to other classes without being their direct parent class.
    Think of it as adding a specific "flavor" or capability to your program.

#### Basic Program Mixin

The [`BasicProgramMixin`][acoupi.programs.templates.BasicProgramMixin] provides a convenient starting point for programs that require fundamental audio recording and management capabilities.
By incorporating this mixin, you can quickly set up a program that captures audio data and organizes recordings efficiently.

To use the `BasicProgramMixin`, import it and include it as a base class along with `AcoupiProgram` when defining your custom program:

```python
from acoupi.programs import AcoupiProgram
from acoupi.programs.templates import BasicProgramMixin, BasicConfiguration

class CustomProgram(BasicProgramMixin, AcoupiProgram):

    config_schema = BasicConfiguration
```

This automatically equips your `CustomProgram` with two essential tasks:

- **Recording Task**: This task handles the core audio recording functionality.
    It checks recording conditions, captures audio segments of a defined duration at specified intervals, and temporarily stores the recordings.
    This task utilizes the `generate_recording_task` template ([`acoupi.tasks.generate_recording_task`][acoupi.tasks.generate_recording_task]) for its implementation.

- **File Management Task**: This task manages the recorded audio files.
    It processes the temporary recordings, determining which recordings to save permanently based on predefined criteria (by default, all recordings are saved).
    Saved recordings are organized in a structured folder hierarchy: `<base_directory>/<year>/<month>/<day>/<time>_<recording_id>.wav`.
    This task is based on the `generate_file_management_task` template ([`acoupi.tasks.generate_file_management_task`][acoupi.tasks.generate_file_management_task]).

The `BasicProgramMixin` uses the `BasicConfiguration` schema ([`acoupi.programs.templates.BasicConfiguration`][acoupi.programs.templates.BasicConfiguration]) to define its configurable parameters.
To extend these parameters, you can create a new configuration class that inherits from `BasicConfiguration` and adds your custom fields:

```python
class ExpandedConfigurations(BasicConfiguration):
    other_field: bool = True
    # ... your additional fields ...
```

While the `BasicProgramMixin` provides a solid foundation, you can further customize its behaviour by overriding specific methods.
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

class CustomProgram(BasicProgramMixin, AcoupiProgram):
    # ... other parts of your program ...

    def get_recording_conditions(self, config):
        # Get the default conditions (e.g., recording interval)
        default_conditions = super().get_recording_conditions(config)
        return [
            *default_conditions,
            IsWarmEnough(config.temperature_threshold)  # Add your custom condition
        ]

```

For a complete understanding of the BasicProgramMixin's capabilities and customization options, refer to its [reference documentation][acoupi.programs.templates.BasicProgramMixin].

#### Messaging Program Mixin

The [`MessagingProgramMixin`][acoupi.programs.templates.MessagingProgramMixin] provides your programs with communication capabilities, enabling them to send messages based on events or data processed by your sensor.

To incorporate messaging functionality into your program, follow a similar approach to the `BasicProgramMixin`:

- **Inherit from the Mixin**: Include `MessagingProgramMixin` as a base class along with `AcoupiProgram` when defining your custom program.
- **Use a Compatible Schema**: Ensure your configuration schema inherits from [`MessagingConfigMixin`][acoupi.programs.templates.MessagingConfigMixin] to include the necessary messaging-related settings.

```python
from acoupi.programs.templates import MessagingProgramMixin, MessagingConfigMixin
from acoupi.programs import AcoupiProgram

class CustomConfig(MessagingConfigMixin):
    # ... your custom configuration fields ...

class CustomProgram(MessagingProgramMixin, AcoupiProgram):

    config_schema = CustomConfig
```

This configuration grants your program the following messaging features:

- **Messenger**: A [`Messenger`][acoupi.components.types.Messenger] object is created, allowing you to choose between HTTP or MQTT protocols for message delivery.
- **Message Store**: A dedicated message store is initialised to keep track of all messages generated by your device, including their delivery status.
- **Send Messages Task**: This periodic task (running every 2 minutes by default, but configurable) checks the message store for pending messages and attempts to deliver them.
    It leverages the [`generate_send_messages_task`][acoupi.tasks.generate_send_messages_task] template for its implementation.
- **Heartbeat Task**: This task periodically sends a heartbeat message (every 30 minutes by default, configurable) containing information about the device's status, ID, and the current time.
    This provides a regular indication that the device is active and functioning correctly.

By default, the `MessagingProgramMixin` doesn't generate any messages on its own.
Its primary purpose is to provide the underlying framework for sending messages.
You can easily create and send messages from your custom tasks using the message_store:

```python
from acoupi.data import Message
import datetime

class CustomProgram(MessagingProgramMixin, AcoupiProgram):

    def setup(self, config):
        super().setup(config)  # Initialize the messaging components

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

For detailed information about the configuration options and customization possibilities of the `MessagingProgramMixin`, consult its comprehensive [reference documentation][acoupi.programs.templates.MessagingProgramMixin].

### Predefined Configuration Schemas

Defining a robust configuration schema is crucial for designing effective and adaptable _acoupi_ programs.
A well-structured schema enhances program flexibility, provides clear guidance to users on configurable options, and ensures that configurations are validated before deployment, preventing potential issues.

While you'll need to create custom schemas for program-specific behaviors, _acoupi_ strongly encourages reusing predefined schemas for common components.
This approach not only saves you time and effort but also ensures compatibility with program templates and benefits from carefully designed and validated schema structures.

_acoupi_ provides a collection of predefined schemas for common components:

1. [**MicrophoneConfig**][acoupi.components.MicrophoneConfig]: This schema facilitates configuration of the microphone device, including device selection, sampling rate, and the number of channels.
      It's highly customized for ease of use during setup, so utilizing it is recommended for streamlined microphone configuration.

2. [**MQTTConfig**][acoupi.components.MQTTConfig] and [**HTTPConfig**][acoupi.components.HTTPConfig]: These schemas streamline the configuration of MQTT and HTTP messengers, respectively, for programs that require communication capabilities.

3. [**PathsConfiguration**][acoupi.programs.templates.PathsConfiguration]: This schema defines options for configuring storage locations for audio recordings and metadata.
      By default, temporary recordings are stored in memory (if available) and permanent recordings are saved in `$HOME/audio/`, but you can customize these paths according to your needs.

4. [**RecordingConfiguration**][acoupi.programs.templates.AudioConfiguration]: This schema covers the essential parameters for the recording task, such as recording duration, recording interval, and scheduling options.

5. [**MessagingConfiguration**][acoupi.programs.templates.MessagingConfig]: This schema encompasses all the necessary settings for configuring the messaging task.

These predefined schemas are further grouped into higher-level schemas for broader functionalities:

1. [**BasicConfiguration**][acoupi.programs.templates.BasicConfiguration]: This schema combines MicrophoneConfig, PathsConfiguration, and RecordingConfiguration, providing all the essential configurations for a basic _acoupi_ program.

2. [**MessagingConfigMixin**][acoupi.programs.templates.MessagingConfigMixin]: This schema includes the necessary configurations for using the MessagingProgramMixin, enabling message sending capabilities in your programs.

Leverage these predefined schemas as building blocks to construct comprehensive configuration schemas tailored to your specific program requirements.
This modular approach promotes consistency, reduces redundancy, and ensures your programs are well-structured and easily configurable.

### Task Templates

### Component Selection
