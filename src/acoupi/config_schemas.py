"""Config module."""
from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace
from pathlib import Path

from pydantic import BaseModel
from typing_extensions import Self


__all__ = [
    "BaseConfigSchema",
]


class CeleryConfig(BaseModel):
    """Celery config."""

    enable_utc: bool = True
    timezone: str = "UTC"
    broker_url: str = "pyamqp://guest@localhost//"
    result_backend: str = "rpc://"
    result_persistent = False
    task_serializer = "pickle"
    result_serializer = "pickle"
    accept_content = ["pickle"]


class BaseConfigSchema(BaseModel, ABC):
    """Base class for config schemas objects."""

    celery: CeleryConfig = CeleryConfig()

    @classmethod
    @abstractmethod
    def add_arguments(cls, parser: ArgumentParser):
        """Define arguments."""
        raise NotImplementedError

    @classmethod
    def from_args(cls, args: list[str]) -> Self:
        """Create config from arguments."""
        parser = ArgumentParser()
        cls.add_arguments(parser)
        parsed_args, _ = parser.parse_known_args(args)
        return cls.from_parsed_args(parsed_args)

    @classmethod
    def from_parsed_args(cls, parsed_args: Namespace) -> Self:
        """Create config from parsed arguments."""
        return cls(**vars(parsed_args))

    def write(self, path: Path):
        """Write config to file in json format."""
        with open(path, "w") as file:
            file.write(self.json())

    @classmethod
    def from_file(cls, path: Path) -> Self:
        """Create config from file."""
        with open(path) as file:
            return cls.parse_raw(file.read())
