"""CLI for acoupi."""

from acoupi.cli.base import acoupi
from acoupi.cli.config import config
from acoupi.cli.deployment import deployment
from acoupi.cli.tasks import task
from acoupi.cli.workers import workers

__all__ = [
    "acoupi",
    "config",
    "deployment",
    "task",
    "workers",
]


if __name__ == "__main__":
    acoupi()
