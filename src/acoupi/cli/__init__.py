"""CLI for acoupi."""

from acoupi.cli.base import acoupi
from acoupi.cli.config import config
from acoupi.cli.deployment import deployment

__all__ = [
    "acoupi",
    "config",
    "deployment",
]


if __name__ == "__main__":
    acoupi()
