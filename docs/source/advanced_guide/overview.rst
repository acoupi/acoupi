.. _advanced-guide-overview:

Overview
========

Here we provide a brief overview of the **Acoupi** framework. We recommend you
to read this section before diving into the details of the framework.

Basic concepts
--------------

**Acoupi** is a framework that allows you to build your own smart monitoring
sensor. The framework is organized into four increasingly complex layers:

1. :ref:`Data<overview_data>`
2. :ref:`Components<overview_components>`
3. :ref:`Tasks<overview_tasks>`
4. :ref:`Programs<overview_programs>`

.. _overview_data:

Data
----

The :ref:`data<advanced-guide-data>` layer is a fundamental part of the
**Acoupi** framework, as it is where all the information handled by the system
is grouped and categorized. The data layer consists of the following three main
objects:

- :ref:`Deployment<advanced-guide-deployments>`: A deployment object contains
  all the information about a specific deployment. This includes information
  about the device, the location where the device is deployed, and the starting
  date.

- :ref:`Recordings<advanced-guide-recordings>`: A recording object represents a
  single recording made by the device. It contains information about the
  recording, such as the date and time when the recording was made, the path to
  the audio file, and the duration of the recording.

- :ref:`Detections<advanced-guide-detections>`: A detection object represents a
  single detection made by some ML model. It contains information about in
  which recording the detection was made, what is the species of the animal
  that was detected, and the probability of the detection.

These objects are used by the other layers of the **Acoupi** framework to perform
their tasks, such as processing, storing, and sending data. By defining these
objects and their properties, the data layer provides a clear and consistent
way of handling information throughout the framework.

.. _overview_components:

Components
----------

A :ref:`component<advanced-guide-components>` is a building block of the
**Acoupi** framework that performs a specific job. For example, a component can
be a sensor that reads the temperature or a component that sends a message to a
server. Components are independent of each other and can be used in different
ways.

The **Acoupi** framework provides a library of built-in components that you can
use to build your own programs. For example, the library provides components to
record audio using a microphone, save machine learning (ML) detections to a
database, and send messages to a remote server. These components have been
thoroughly tested and are ready to be used in your programs. Please check the
:ref:`components library<advanced-guide-component-library>` section for a
complete list of built-in components.

Additionally, **Acoupi** allows you to create your own custom components. For
example, you can create a component that reads the temperature from a sensor.
We have included a design guide for creating your own components in a way that
is compatible with the **Acoupi** framework. Please check the :ref:`custom
components<advanced-guide-custom-components>` section for more details.

.. _overview_tasks:

Tasks
-----

A :ref:`task<advanced-guide-tasks>` is a sequence of commands that are executed
following a specific flow. Each task is meant to be run by the device,
potentially in parallel, and can be used to perform a specific function. For
example, a task can be used record audio when specific conditions are met and
save the audio in the filesystem. Task are generally built using components,
but can also include custom code.

**Acoupi** provides tools to create tasks based on preset templates. For
example, you can create a ``process_audio`` task that runs a sequence of
machine learning models to detect specific sounds in the latest recording and
stores relevant detections in a database. It is possible to provide custom
components to the templates to further customise the task, while keeping the
same standard structure. Please check the :ref:`tasks<advanced-guide-tasks>`
section for more details.

.. _overview_programs:

Programs
--------

A :ref:`program<advanced-guide-programs>` is a full application that runs on
the device. A program is composed of one or more tasks. Some tasks run
periodically, while others are triggered by other tasks. Once the program
starts running, it will autonomously perform the tasks that have been defined.

**Acoupi** provides some prebuilt programs that you can use to monitor your
with device. However you can also create your own programs to customise the
behaviour of your device. Please check the
:ref:`programs<advanced-guide-programs>` section for more details.
