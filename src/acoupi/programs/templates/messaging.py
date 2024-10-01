"""Messaging Program template module.

This module provides a template for adding messaging capabilities to Acoupi
programs.

It includes:

- **MessagingProgramMixin:**  A mixin class that provides functionality for
  sending messages and heartbeats.
- **Configuration Schemas:** Defines the configuration schemas
  (`MessagingConfig` and `MessagingConfigMixin`) for configuring messaging
  settings, including message store location, message sending interval,
  heartbeat interval, and messenger configurations (HTTP or MQTT).

To use this template:

1. Create a new program class that inherits from `MessagingProgramMixin`.
2. Include `MessagingConfigMixin` in your program's configuration schema.
3. Configure the `messaging` settings in your program's configuration.

This will add messaging capabilities to your program, allowing it to send
messages and heartbeats via the configured messenger (HTTP or MQTT).
"""

from pathlib import Path
from typing import Optional, TypeVar

from pydantic import BaseModel, Field, model_validator

from acoupi import tasks
from acoupi.components import SqliteMessageStore, messengers, types
from acoupi.programs.core import ProgramProtocol


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

    heartbeat_interval: int = 60
    """Interval between sending heartbeats in seconds."""

    http: Optional[messengers.HTTPConfig] = None
    """HTTP messenger configuration."""

    mqtt: Optional[messengers.MQTTConfig] = None
    """MQTT messenger configuration."""

    @model_validator(mode="after")
    def validate_messaging_config(self):
        if self.http is None and self.mqtt is None:
            raise ValueError("No messenger configuration provided.")
        return self


class MessagingConfigMixin(BaseModel):
    """Messaging configuration mixin.

    This mixin includes the `MessagingConfig` schema in the program's
    configuration.
    """

    messaging: MessagingConfig


ProgramConfig = TypeVar("ProgramConfig", bound=MessagingConfigMixin)


class MessagingProgramMixin(ProgramProtocol[ProgramConfig]):
    """Messaging program mixin.

    This mixin provides functionality for sending messages and heartbeats
    to a configured messenger (HTTP or MQTT).
    """

    messenger: types.Messenger
    """The configured messenger instance."""

    message_store: types.MessageStore
    """The configured message store instance."""

    def setup(self, config: ProgramConfig):
        """Set up the messaging program mixin.

        This method initializes the message store and messenger, registers
        the messaging and heartbeat tasks, and performs any necessary setup.
        """
        self.message_store = self.configure_message_store(config)
        self.messenger = self.configure_messenger(config)
        self.register_messaging_task(config)
        self.register_heartbeat_task(config)
        super().setup(config)

    def check(self, config: ProgramConfig) -> None:
        """Check the messenger connection.

        This method checks the connection to the configured messenger
        (HTTP or MQTT).
        """
        if isinstance(self.messenger, messengers.HTTPMessenger):
            self.messenger.check()

        if isinstance(self.messenger, messengers.MQTTMessenger):
            self.messenger.check()

        super().check(config)

    def configure_message_store(
        self, config: ProgramConfig
    ) -> types.MessageStore:
        """Configure the message store.

        This method creates and configures an instance of the
        `SqliteMessageStore` based on the provided configuration.

        Returns
        -------
        types.MessageStore
            The configured message store instance.
        """
        return SqliteMessageStore(config.messaging.messages_db)

    def configure_messenger(self: ProgramProtocol, config: ProgramConfig):
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

        raise ValueError("No messenger configuration provided.")

    def create_messaging_task(self, config: ProgramConfig):
        """Create the messaging task.

        This method creates the task responsible for sending messages.

        Returns
        -------
        Callable
            The messaging task.
        """
        return tasks.generate_send_messages_task(
            message_store=self.message_store,
            messengers=[self.messenger],
            logger=self.logger.getChild("messaging"),
        )

    def create_heartbeat_task(self, config: ProgramConfig):
        """Create the heartbeat task.

        This method creates the task responsible for sending heartbeats.

        Returns
        -------
        Callable
            The heartbeat task.
        """
        return tasks.generate_heartbeat_task(
            messengers=[self.messenger],
            logger=self.logger.getChild("heartbeat"),
        )

    def register_messaging_task(self, config: ProgramConfig):
        """Register the messaging task.

        This method registers the messaging task with the program's scheduler.
        """
        messaging_task = self.create_messaging_task(config)
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
        self.add_task(
            heartbeat_task,
            schedule=config.messaging.heartbeat_interval,
            queue="celery",
        )
