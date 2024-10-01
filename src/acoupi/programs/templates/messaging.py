from pathlib import Path
from typing import Optional, TypeVar

from pydantic import BaseModel, Field, model_validator

from acoupi import tasks
from acoupi.components import SqliteMessageStore, messengers, types
from acoupi.programs.core import ProgramProtocol


class MessagingConfig(BaseModel):
    messages_db: Path = Field(
        default=Path.home() / "storages" / "messages.db",
    )

    message_send_interval: int = 120

    heartbeat_interval: int = 60

    http: Optional[messengers.HTTPConfig] = None

    mqtt: Optional[messengers.MQTTConfig] = None

    @model_validator(mode="after")
    def validate_messaging_config(self):
        if self.http is None and self.mqtt is None:
            raise ValueError("No messenger configuration provided.")
        return self


class MessagingConfigMixin(BaseModel):
    messaging: MessagingConfig


ProgramConfig = TypeVar("ProgramConfig", bound=MessagingConfigMixin)


class MessagingProgramMixin(ProgramProtocol[ProgramConfig]):
    messenger: types.Messenger

    message_store: types.MessageStore

    def setup(self, config: ProgramConfig):
        self.message_store = self.configure_message_store(config)
        self.messenger = self.configure_messenger(config)
        self.register_messaging_task(config)
        self.register_heartbeat_task(config)
        super().setup(config)

    def check(self, config: ProgramConfig) -> None:
        if isinstance(self.messenger, messengers.HTTPMessenger):
            self.messenger.check()

        if isinstance(self.messenger, messengers.MQTTMessenger):
            self.messenger.check()

        super().check(config)

    def configure_message_store(
        self, config: ProgramConfig
    ) -> types.MessageStore:
        return SqliteMessageStore(config.messaging.messages_db)

    def configure_messenger(self: ProgramProtocol, config: ProgramConfig):
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
        return tasks.generate_send_messages_task(
            message_store=self.message_store,
            messengers=[self.messenger],
            logger=self.logger.getChild("messaging"),
        )

    def create_heartbeat_task(self, config: ProgramConfig):
        return tasks.generate_heartbeat_task(
            messengers=[self.messenger],
            logger=self.logger.getChild("heartbeat"),
        )

    def register_messaging_task(self, config: ProgramConfig):
        messaging_task = self.create_messaging_task(config)
        self.add_task(
            messaging_task,
            schedule=config.messaging.message_send_interval,
            queue="celery",
        )

    def register_heartbeat_task(self, config: ProgramConfig):
        heartbeat_task = self.create_heartbeat_task(config)
        self.add_task(
            heartbeat_task,
            schedule=config.messaging.heartbeat_interval,
            queue="celery",
        )
