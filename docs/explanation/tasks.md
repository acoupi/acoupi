# Tasks (acoupi framework)

Tasks are individual units of work performing a set of specific actions. These are built as a sequence of one or more _acoupi_ components. 
The _acoupi_ framework defines 6 tasks recording, detection, messaging, management, summary, and heartbeat. 

## Overview Tasks

??? Example "a dummy acoupi task"

    ```python
    import logging
    from typing import Optional

    from acoupi import data
    from acoupi.components import types

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    def generate_dummy_acoupi_task(
        component_1: types.DummyComponent1,
        component_2: types.DummyComponent2,
        logger: logging.Logger = logger, 
    ) -> Optional[data.DataSchema]:
        """Generate a dummy task using various acoupi components."""

        def dummy_acoupi_task() -> Optional[data.DataSchema]:
            """Create the structure of a dummy task."""

            output = component_1.associated_method_one()
            result = component_2.associated_method_two(output)

            logger.info(f"Dummy Task result is: {result}")

        return dummy_acoupi_task
    ```

#### Recording

The [Recording](../reference/tasks.md) task is responsible for recording an audio file and storing the metadata in the store.
The recording task builds upon the acoupi components: `AudioRecorder` to capture the audio, `RecordingCondition` to determine whether a recording should occur, and `Store` to save the metadata of a recording.

<figure markdown="span">
    ![Figure 1: Overview of the recording task](../img/task_01_audiorecording.png){ width="110%" }
    <figcaption><b>Example of the audio recording task.</b> The audio recording is made of various acoupi components: RecordingCondition, RecordingScheduler, AudioRecording, and Store.
</figure>

!!! Example "Structure of a recording task"

    ```python
    from acoupi import components, tasks

    recording_task = tasks.generate_recording_task(
        recorder=components.PyAudioRecorder(),
        store=components.SqliteStore(),
        recording_conditions=components.IsInInterval(),
        logger=logger.getChild("recording"),
    )

    ```

#### Detection

The [Detection](../reference/tasks.md) task is responsible for processing audio files.
The task builds upon the acoupi components: `ProcessingFilter` to determine if a recording should be processed, `Model` to run an audio classifier model, `ModelOutputCleaner` to cleans the model outputs, `MessageBuilder` to generate messages with the detected information, and `Store` and `MessageStore` to save the metadata of the procesed recordings and store the messages to be sent.

<figure markdown="span">
    ![Figure 2: Overview of the detection task](../img/task_02_model.png){ width="110%" }
    <figcaption><b>Example of the detection task.</b> The detection process audio recordings, it is made of various acoupi components: Model, ModelOutputCleaner, Store, MessageBuilder, and MessageStore.
</figure>

!!! Example "Structure of a detection task using BatDetect2 classifier"

    ```python
    from typing import Optional

    from acoupi import components, data, tasks
    
    from acoupi_batdetect2.model import BatDetect2

    recording_task = tasks.generate_detection_task(
        store=components.SqliteStore(),
        model=BatDetect2()
        message_store=components.SqliteMessageStore(),
        message_factories=[components.FullModelOutputMessageBuilder()],
        logger=logger.getChild("detection"),
        output_cleaners=Optional[components.ThresholdDetectionCleaner()],
    )
    ```

#### Messaging

The [Messaging](../reference/tasks.md) task is responsible responsible for communication with a remote server.
It uses the `Messenger` component to define the communication protocol for sending messages, and the `MessageStore` component to check if there are any pending messages to need to be sent.

#### Management

The [Management](../reference/tasks.md) task is responsible for managing recording files.
It handles the saving, deletion, and movement of files using the `SavingFilters` and `SavingManagers` components, and keep track of files movements by updating the store.


<figure markdown="span">
    ![Figure 3: Overview of the messaging and management tasks](../img/task_0304_message_management.png){ width="110%" }
    <figcaption><b>Example of the messaging and management tasks.</b> The message task sends messages to a remote server, while the management task handles the movement, saving, and deletion of recordings. Components used in both tasks include: Messenger, SavingFilters, SavingManagers, Store, and MessageStore.
</figure>

#### Summary

The [Summary](../reference/tasks.md) task is responsible for generating summary messages to be sent to a remote server. It uses the `Summariser` component along with the `Messenger` component to define the communication protocol for sending these messages. 

The summary task is useful for providing aggregated information on detections over specific time periods such as hourly, daily, or weekly.

#### Heartbeat

The [Heartbeat](../reference/tasks.md) task is responsible for creating and sending heartbeat to a remote server. Heartbeat messages confirm that a remotely deployed device is up and running. They are sent at regular intervals so that if a message isn't received as expected, the user is alerted that there might be an issue with the system, such as a power outage or loss of connectivity.

By default, a heartbeat message contains two key pieces of information: the device ID and the timestamp when the message was created and sent. The task uses the `Messenger` component to define the communication protocol for sending these messages.

Heartbeat tasks are also useful for sending updates like program status or daily reports, including details about available storage and battery capacity.


## Understanding Tasks 

In an acoupi program, tasks are characterised by three elements:

- **Function**: The functionality of the task. This is the sequence of _acoupi_ components specifiying what actions the task perform.
- **Schedule**: When and how often the task runs (e.g., continuously, at specific intervals, triggered by an event).
- **Dependencies**: How the task relates to other tasks in the program (e.g., does it need to run before or after another task?).

??? info

    Please refer to [_Explanation: System Section_](../explanation/system.md) to learn more about the registration and orchestration of the tasks in an acoupi program using the Celery app.