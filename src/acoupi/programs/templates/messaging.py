"""Messaging Program template module.

This module provides a base class (`MessagingProgram`) for creating Acoupi
programs with messaging capabilities. It extends the `BasicProgram` class to
add functionality for sending messages and heartbeats.

Components:

- **Messenger:**  A component responsible for sending messages and heartbeats
  via a configured communication protocol (HTTP or MQTT).
- **Message Store:** A database for storing messages before they are sent.

Tasks:

Using the components above, `MessagingProgram` creates and manages the
following tasks:

- **Heartbeat Task:** Periodically sends heartbeat messages to indicate that
  the program is running.
- **Send Messages Task:**  Periodically sends messages from the message store
  with the configured messenger.

This program includes all the functionality of
[`BasicProgram`][acoupi.programs.templates.BasicProgram], inheriting its
components and tasks for audio recording, metadata storage, and file
management.

Usage:

To create an Acoupi program with messaging capabilities, define a new class
that inherits from `MessagingProgram` and configure it using the
`MessagingProgramConfiguration` schema.
"""

from pathlib import Path
from typing import Callable, Optional, TypeVar

from pydantic import BaseModel, Field

from acoupi import data, tasks
from acoupi.components import SqliteMessageStore, messengers, types
from acoupi.programs.templates.basic import (
    BasicProgram,
    BasicProgramConfiguration,
)


class MessagingConfig(BaseModel):
    """Messaging configuration schema.

    This schema defines the configuration for messaging components, including
    the message store, message sending interval, heartbeat interval, and
    messenger configurations (HTTP or MQTT).
    """

    messages_db: Path = Field(
        default=Path.home() / "storages" / "messages.db",
    )
    """Path to the message database."""

    message_send_interval: int = 120
    """Interval between sending messages in seconds."""

    heartbeat_interval: int = 60 * 60
    """Interval between sending heartbeats in seconds."""

    http: Optional[messengers.HTTPConfig] = None
    """HTTP messenger configuration."""

    mqtt: Optional[messengers.MQTTConfig] = None
    """MQTT messenger configuration."""


class MessagingProgramConfiguration(BasicProgramConfiguration):
    """Messaging Program Configuration schema.

    This schema extends the `BasicProgramConfiguration` to include settings
    for messaging functionality.
    """

    messaging: MessagingConfig


ProgramConfig = TypeVar("ProgramConfig", bound=MessagingProgramConfiguration)


class MessagingProgram(BasicProgram[ProgramConfig]):
    """Messaging Acoupi Program.

    This class extends the `BasicProgram` to provide functionality for
    sending messages and heartbeats with a configured messenger (HTTP or MQTT).

    Components:

    - **Messenger:** A component responsible for sending messages and
      heartbeats via a configured communication protocol (HTTP or MQTT).
    - **Message Store:** A database for storing messages before they are sent.

    Tasks:

    Using the components above, this class creates and manages the following
    tasks:

    - **Heartbeat Task:** Periodically sends heartbeat messages to indicate
      that the program is running.
    - **Send Messages Task:** Periodically sends messages from the message
      store to the configured messenger.

    This program includes all the functionality of
    [`BasicProgram`][acoupi.programs.templates.BasicProgram], inheriting its
    components and tasks for audio recording, metadata storage, and file
    management.
    """

    messenger: Optional[types.Messenger]
    """The configured messenger instance."""

    message_store: types.MessageStore
    """The configured message store instance."""

    def setup(self, config: ProgramConfig):
        """Set up the Messaging Program.

        This method initialises the message store and messenger, registers
        the messaging and heartbeat tasks, and performs any necessary setup.
        """
        self.validate_dirs(config)
        self.message_store = self.configure_message_store(config)
        self.messenger = self.configure_messenger(config)
        self.register_messaging_task(config)
        self.register_heartbeat_task(config)
        super().setup(config)

    def on_end(self, deployment: data.Deployment) -> None:
        """End a deployment.

        This method is called when the program is stopped. It updates the
        deployment information in the metadata store, and ensure and performs
        any necessary cleanup tasks (i.e., file_management_task, messaging_task).
        """
        super().on_end(deployment)

        if self.messenger is None:
            return

        print("Running messaging task to send remaining messages.")
        self.tasks["messaging_task"].apply()

    def check(self, config: ProgramConfig) -> None:
        """Check the messenger connection.

        This method checks the connection to the configured messenger
        (HTTP or MQTT).
        """
        check_messenger = getattr(self.messenger, "check", None)
        if callable(check_messenger):
            check_messenger()

        super().check(config)

    def configure_message_store(self, config: ProgramConfig) -> types.MessageStore:
        """Configure the message store.

        This method creates and configures an instance of the
        `SqliteMessageStore` based on the provided configuration.

        Returns
        -------
        types.MessageStore
            The configured message store instance.
        """
        return SqliteMessageStore(config.messaging.messages_db)

    def configure_messenger(self, config: ProgramConfig):
        """Configure the messenger.

        This method creates and configures an instance of the
        `HTTPMessenger` or `MQTTMessenger` based on the provided
        configuration.

        Returns
        -------
        types.Messenger
            The configured messenger instance.

        Raises
        ------
        ValueError
            If no messenger configuration is provided.
        """
        if config.messaging.http is not None:
            return messengers.HTTPMessenger.from_config(
                config.messaging.http,
            )

        if config.messaging.mqtt is not None:
            return messengers.MQTTMessenger.from_config(
                config.messaging.mqtt,
            )

        return None

    def create_messaging_task(self, config: ProgramConfig):
        """Create the messaging task.

        This method creates the task responsible for sending messages.

        Returns
        -------
        Callable
            The messaging task.
        """
        if self.messenger is None:
            return

        return tasks.generate_send_messages_task(
            message_store=self.message_store,
            messengers=[self.messenger],
            logger=self.logger.getChild("messaging"),
        )

    def create_heartbeat_task(self, config: ProgramConfig) -> Optional[Callable]:
        """Create the heartbeat task.

        This method creates the task responsible for sending heartbeats.

        Returns
        -------
        Callable
            The heartbeat task.
        """
        if self.messenger is None:
            return

        return tasks.generate_heartbeat_task(
            messengers=[self.messenger],
            logger=self.logger.getChild("heartbeat"),
        )

    def register_messaging_task(self, config: ProgramConfig):
        """Register the messaging task.

        This method registers the messaging task with the program's scheduler.
        """
        messaging_task = self.create_messaging_task(config)

        if messaging_task is None:
            return

        self.add_task(
            messaging_task,
            schedule=config.messaging.message_send_interval,
            queue="celery",
        )

    def register_heartbeat_task(self, config: ProgramConfig):
        """Register the heartbeat task.

        This method registers the heartbeat task with the program's scheduler.
        """
        heartbeat_task = self.create_heartbeat_task(config)

        if heartbeat_task is None:
            return

        self.add_task(
            heartbeat_task,
            schedule=config.messaging.heartbeat_interval,
            queue="celery",
        )

    def validate_dirs(self, config: ProgramConfig):
        """Validate the directories used by the program.

        This method ensures that the necessary directories for storing audio
        and metadata exist. If they don't, it creates them.
        """
        if not config.messaging.messages_db.parent.exists():
            config.messaging.messages_db.parent.mkdir(parents=True)
