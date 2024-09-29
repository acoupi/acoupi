# Architecture Overview

Here we provide a brief overview of the **acoupi** framework. We recommend you
to read this section before diving into the details of the framework. 

## Basic concepts

**acoupi** is a framework that allows you to build your own smart monitoring
sensor. The framework is organized into four increasingly complex layers:

1. [Data Schema](#data-schema)
2. [Components](#components)
3. [Tasks](#tasks)
4. [Programs](#programs)

![Figure 1: Overview of acoupi layers](../img/acoupi_four_layers_architecture.png) *Figure 1: Overview of the layered architecture of acoupi. From bottom to top the layers are (1) the data schema, (2) the components, (3) the tasks, (4) the programs.*

## Data Schema

The [**Data Schema**](../developer_guide/data_schema.md) layer is a fundamental
part of the **acoupi** framework, as it is where all the information handled by
the system is grouped and categorized.

The data objects are used by the other layers of the **acoupi** framework. By
defining the data objects and their properties, the data layer provides a clear
and consistent way of handling information throughout the framework. 

The data schema objects corresponds to attributes of Python classes and are built using the Pydantic library. 

## Components 

The [**Components**](../developer_guide/components.md) layer form the building blocks of acoupi. Each component (i.e., Python class) has a single responsibility and performs a specific action. 

**acoupi** provides a library of built-in components that can be used to build
custom programs. The library provides components to record audio using a
microphone, save machine learning (ML) detections to a database, and send
messages to a remote server. These components have been thoroughly tested and
are ready to be used. 

Additionally, **acoupi** allows you to create your own custom components. For
example, you can create a new component that would read the temperature from a
sensor. We have included a design guide for creating your own components in a
way that is compatible with the **acoupi** framework. 

Please check the
[**Components**](../developer_guide/components.md) section for a  list of the built-in components and details about developing your own. 

## Tasks

The [**Tasks**](../developer_guide/tasks.md) are sequences of one or more
acoupi components executed in a specific flow. The **acoupi** framework defines
4-core tasks: recording, detection, messaging, and management to formulate a
complete AIoT bioacoustics sensor.

**Acoupi** provides tools to create tasks based on preset templates. For
example, you can create a novel task that runs a sequence of machine learning
models to detect specific sounds in the latest recording and stores relevant
detections in a database. It is possible to provide custom components to the
templates to further customise the task, while keeping the same standard
structure. Please check the [**Tasks**](../developer_guide/tasks.md) section
for more details.

## Programs

A [**Program**](../developer_guide/programs.md) is a full application that runs
on the device. A program is composed of one or more tasks. Some tasks run
periodically, while others are triggered by other tasks. Once the program starts
running, it will autonomously perform the tasks that have been defined.

**Acoupi** provides currently two prebuilt programs that you can use to monitor
your with device. The
[**BatDetect2**](https://github.com/acoupi/acoupi_batdetect2) program allow you
to record and classify UK Bats species while the
[**BirdNET**](https://github.com/acoupi/acoupi_batdetect2) program can be used
for identify bird species. Please check their related documentation for more
details.

You can also create your own programs to customise the behaviour of your device.
Please check the [**Program**](../developer_guide/programs.md) section for more
details.

## Example 

#### Configured acoupi program

Acoupi framework is built around the ability in Python programming to define reusable templates that keep away the internal methods from a user. The so-called abstraction feature ([Python PEP 3119](https://peps.python.org/pep-3119/)). The layered architecture allow to break elements of acoustic monitoring surveys into reusable and configurable pieces. 

In the diagram below, we provide an example of an implemented acoupi program. This diagram shows the *abstract* components and their related implemented components (i.e., the subclasses). 

![Figure 2.1: A configured acoupi program - Task A: Audio Recording](../img/task_01_audiorecording.png)
![Figure 2.2: A configured acoupi program Task B: Model](../img/task_02_model.png)
![Figure 2.3: A configured acoupi program Task C: Message and Management](../img/task_0304_message_management.png)


*Figure 2: Example of a configured acoupi program. The four tasks of audio recordings, detections, messaging and management are composed of a series of components. Each task shows the abstract classes of the component and its relative subclasses. The component executes one to multiple functions that return a data object defined by the acoupi data schema. The figure shows how some of the components can be reused through the different tasks (i.e., the MessageStore and the Store component).*

