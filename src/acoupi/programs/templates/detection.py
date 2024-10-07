"""Detection Program template module.

This module provides a base class (`DetectionProgram`) for creating Acoupi
programs that perform audio detection tasks. It extends the `MessagingProgram`
class to add detection capabilities.

Key Components:

- **Detection Model:** An audio detection model that processes recordings to
  identify specific sounds or events.

Tasks:

- **Detection Task:** Runs the detection model on audio recordings and
  processes the results, including generating messages based on detected
  events.

Features:

- **Messaging Features:** Inherits all features from `MessagingProgram`,
  including:
    - **Messaging:** Sends messages and heartbeats to a configured messenger
      (HTTP or MQTT).
    - **Message Store:** A database for storing messages before they are sent.
- **Basic Program Features:** Inherits all features from `BasicProgram`,
  including:
    - **Audio Recording:** Records audio clips at regular intervals.
    - **Metadata Storage:** Stores metadata associated with recordings in a
      SQLite database.
    - **File Management:** Manages the storage of audio recordings, saving
      them to permanent storage and handling temporary files.

Usage:

To create an Acoupi program with audio detection capabilities:

1. Define a new class that inherits from `DetectionProgram`.
2. Define a configuration schema that inherits from
   `DetectionProgramConfiguration`.
3. Implement the `configure_model` method to configure your detection model.
4. Optionally override the following methods to customise the detection
   process:
    - `get_output_cleaners`:  To clean up the model's raw output.
    - `get_processing_filters`:  To filter recordings before processing.
    - `get_message_factories`:  To customise the messages generated based on
      detection results.
"""

from abc import ABC, abstractmethod
from typing import Callable, List, TypeVar

from pydantic import BaseModel

from acoupi import data
from acoupi.components import types
from acoupi.programs.templates.messaging import (
    MessagingProgram,
    MessagingProgramConfiguration,
)
from acoupi.tasks import generate_detection_task

ModelConfig = TypeVar("ModelConfig", bound=BaseModel)


class DetectionProgramConfiguration(
    MessagingProgramConfiguration,
):
    """Detection Program Configuration schema.

    This schema extends the `MessagingProgramConfiguration` to include any
    additional settings required for detection programs.
    """


C = TypeVar("C", bound=DetectionProgramConfiguration)


class DetectionProgram(MessagingProgram[C], ABC):
    """Detection Program.

    This abstract class extends the `MessagingProgram` to provide a foundation
    for detection programs. It includes functionality for configuring and
    running a detection model, processing model outputs, and generating
    messages based on detection results.

    Components:

    - **Detection Model:** An audio detection model that processes recordings
      to identify specific sounds or events.

    Tasks:

    - **Detection Task:** Runs the detection model on audio recordings and
      processes the results, including:
        - Cleaning the model output using `get_output_cleaners`.
        - Filtering the processed output using `get_processing_filters`.
        - Generating messages based on the results using
          `get_message_factories`.

    Inherited Components:

    This class inherits the following components from `MessagingProgram`:

    - **Messenger:** A component responsible for sending messages and
      heartbeats via a configured communication protocol (HTTP or MQTT).
    - **Message Store:** A database for storing messages before they are sent.

    This class also inherits the following components from `BasicProgram`:

    - **Audio Recorder:** Records audio clips according to the program's
      configuration.
    - **File Manager:** Manages the storage of audio recordings, including
      saving them to permanent storage and handling temporary files.
    - **Store:** Provides an interface for storing and retrieving metadata
      associated with the program and its recordings.

    Inherited Tasks:

    This program inherits the following tasks from `MessagingProgram`:

    - **Heartbeat Task:** Periodically sends heartbeat messages to indicate
      that the program is running.
    - **Send Messages Task:** Periodically sends messages from the message
      store to the configured messenger.

    This program also inherits the following tasks from `BasicProgram`:

    - **Audio Recording:**  Records audio at regular intervals, configurable
      through the `audio` settings in the `BasicProgramConfiguration` schema.
    - **File Management:**  Periodically performs file management operations,
      such as moving recordings from temporary to permanent storage.

    Customization:

    You can customise the detection process by overriding the following
    methods:

    - `configure_model`:  **Required.** Implement this method to configure
      and return an instance of your detection model.
    - `get_output_cleaners`:  To clean up the model's raw output.
    - `get_processing_filters`:  To filter recordings before processing.
    - `get_message_factories`:  To customise the messages generated based on
      detection results.

    Examples
    --------
    ```python
    from acoupi.programs.templates import (
        DetectionProgram,
        DetectionProgramConfiguration,
    )
    from acoupi.components import types

    # This import should be replaced with your actual model import
    # This model does not exist in the acoupi package
    from acoupi.models import SimpleBirdModel


    class MyBirdDetectionConfiguration(
        DetectionProgramConfiguration
    ):
        # Add any configuration specific to bird detection
        pass


    class MyBirdDetectionProgram(
        DetectionProgram[MyBirdDetectionConfiguration]
    ):
        configuration_schema = MyBirdDetectionConfiguration

        def configure_model(
            self, config: MyBirdDetectionConfiguration
        ) -> types.Model:
            return (
                SimpleBirdModel()
            )  # Replace with your actual model
    ```
    """

    model: types.Model
    """The configured detection model instance."""

    def setup(self, config: C) -> None:
        """Set up the Detection Program.

        This method initialises the detection model and performs any
        necessary setup.
        """
        self.model = self.configure_model(config)
        super().setup(config)

    def check(self, config: C):
        """Check the program's components.

        This method performs checks on the program's components, including
        the detection model, to ensure they are functioning correctly.

        Parameters
        ----------
        config : C
            The program's configuration.
        """
        model_check = getattr(self.model, "check", None)
        if model_check and callable(model_check):
            model_check()

        super().check(config)

    @abstractmethod
    def configure_model(self, config: C) -> types.Model:
        """Configure the detection model.

        This method must be implemented by subclasses to configure and return
        an instance of the detection model.

        Parameters
        ----------
        config : C
            The program's configuration.

        Returns
        -------
        types.Model
            The configured detection model instance.
        """

    def get_output_cleaners(self, config: C) -> List[types.ModelOutputCleaner]:
        """Get the model output cleaners.

        This method can be overridden to define a list of output cleaners that
        will be applied to the model's raw output to clean it up or extract
        relevant information.

        Parameters
        ----------
        config : C
            The program's configuration.

        Returns
        -------
        List[types.ModelOutputCleaner]
            A list of model output cleaners.
        """
        return []

    def get_processing_filters(
        self,
        config: C,
    ) -> List[types.ProcessingFilter]:
        """Get the processing filters.

        This method can be overridden to define a list of processing filters
        that will be applied to each recording *before* it is processed by the
        model. These filters determine whether a recording should be processed
        at all.

        This can be useful to avoid unnecessary model processing when it is not
        required by the context or based on simple heuristics on the recording
        content. Model processing can be computationally expensive, so it is
        beneficial to avoid it if possible.

        Parameters
        ----------
        config : C
            The program's configuration.

        Returns
        -------
        List[types.ProcessingFilter]
            A list of processing filters.
        """
        return []

    def get_message_factories(self, config: C) -> List[types.MessageBuilder]:
        """Get the message factories.

        This method can be overridden to define a list of message factories
        that will be used to generate messages based on the processed
        detection results.

        Parameters
        ----------
        config : C
            The program's configuration.

        Returns
        -------
        List[types.MessageBuilder]
            A list of message factories.
        """
        return []

    def create_detection_task(
        self,
        config: C,
    ) -> Callable[[data.Recording], None]:
        """Create the detection task.

        This method creates the task responsible for running the detection
        model and processing its output.

        Parameters
        ----------
        config : C
            The program's configuration.

        Returns
        -------
        Callable[[data.Recording], None]
            The detection task.

        Notes
        -----
        This method uses the `generate_detection_task` function to create the
        detection task. You can override this method to customise the task
        creation process.
        """
        return generate_detection_task(
            store=self.store,
            model=self.model,
            message_store=self.message_store,
            logger=self.logger.getChild("detection"),
            output_cleaners=self.get_output_cleaners(config),
            processing_filters=self.get_processing_filters(config),
            message_factories=self.get_message_factories(config),
        )

    def get_recording_callbacks(self, config: C) -> List[Callable]:
        """Get the recording callbacks.

        This method adds the detection task as a callback to be executed
        after each recording is completed.

        Parameters
        ----------
        config : C
            The program's configuration.

        Returns
        -------
        List[Callable]
            A list of recording callbacks, including the detection task.
        """
        return [self.create_detection_task(config)]

    def get_required_models(self, config: C) -> list[str]:
        name = getattr(self.model, "name", None)
        if name is not None:
            return [name]

        name = getattr(self.model, "__name__", None)
        if name is not None:
            return [name]

        raise ValueError("Model must have a name attribute.")
