from pathlib import Path

from pydantic import BaseModel, Field

from acoupi import components
from acoupi.components import types


class MessagingConfig(BaseModel):
    db: Path = Field(
        default_factory=lambda: Path.home() / "storages" / "messages.db",
    )


class MessagingConfigMixin(BaseModel):
    messaging: MessagingConfig = Field(default_factory=MessagingConfig)


class MessagingProgramMixin(BaseModel):
    messenger: types.Messenger
