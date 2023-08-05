"""Config module."""
from pathlib import Path
from typing import Annotated, List

from pydantic import BaseModel, Field
from typing_extensions import Self

__all__ = [
    "BaseConfigSchema",
    "NoUserPrompt",
]


class NoUserPrompt:
    """No user prompt annotation.

    Use this class to annotate fields that should not be prompted to the user.
    """


class CeleryConfig(BaseModel):
    """Celery config."""

    enable_utc: bool = True
    timezone: str = "UTC"
    broker_url: str = "pyamqp://guest@localhost//"
    result_backend: str = "rpc://"
    result_persistent: bool = False
    task_serializer: str = "pickle"
    result_serializer: str = "pickle"
    accept_content: List[str] = ["pickle"]


class BaseConfigSchema(BaseModel):
    """Base class for config schemas objects."""

    celery: Annotated[CeleryConfig, NoUserPrompt] = Field(
        default_factory=CeleryConfig,
        description="Celery configuration.",
    )

    def write(self, path: Path):
        """Write config to file in json format."""
        with open(path, "w") as file:
            file.write(self.model_dump_json())

    @classmethod
    def from_file(cls, path: Path) -> Self:
        """Create config from file."""
        with open(path) as file:
            return cls.model_validate_json(file.read())
