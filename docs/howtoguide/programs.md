# Create a custom Program

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
This schema specifies the options users can adjust to customize the program's behavior.
In this example, the schema includes a single field called name (of type str) with a default value of "acoupi".
Pydantic offers valuable features like data validation and type hints, ensuring that configuration values are valid and match the expected types.

I then specify that this is the configuration schema for the custom program by defining the `config_schema` field in the program class.

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
The second argument, schedule, determines how the task is executed`.
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

_acoupi_ offers several approaches to facilitate custom program creation:

- **Program Templates**: Leverage pre-defined templates with commonly used tasks and components to expedite development.
- **Predefined Schemas**: Utilize existing schemas for typical program components, saving time and effort in defining configuration options.
- **Task Templates**: Employ templates for frequently used tasks, such as recording audio or sending data, as building blocks for your program.
- **Component Selection**: Modify existing tasks by replacing default components with alternatives or custom implementations to tailor functionality.

Now we will explore each of these methods, giving insight into how to create custom programs within the acoupi framework.

### Program Templates

### Predefined Configuration Schemas

### Task Templates

### Component Selection
