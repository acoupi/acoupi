"""Acoupi Workers CLI Commands.

This module provides command-line interface (CLI) commands for manually
managing Acoupi workers.

While _acoupi_ primarily relies on systemd for robust worker management in
deployments (initiated via `acoupi deployment start`), these commands offer
direct control over worker processes for testing and debugging purposes.

With these commands, you can:

- **Start Workers:** Manually launch worker processes to handle task execution.
- **Restart Workers:**  Restart workers to apply configuration
    changes or troubleshoot issues.
- **Stop Workers:**  Safely shut down worker processes.

This manual control can be valuable in development and testing scenarios where
interacting directly with the workers is necessary.
"""

import click

from acoupi import system
from acoupi.cli.base import acoupi

__all__ = [
    "workers",
]


@acoupi.group()
@click.pass_context
def workers(ctx):
    """Manage acoupi workers.

    Provides subcommands to manually control the Celery workers responsible for
    executing program tasks.
    """
    settings = ctx.obj["settings"]
    if not system.is_configured(settings):
        raise click.UsageError(
            "Acoupi is not setup. Run `acoupi setup` first."
        )


@workers.command()
@click.pass_context
def start(ctx):
    """Start the Celery workers.

    Manually starts the worker processes that handle the execution of program
    tasks.
    """
    settings: system.Settings = ctx.obj["settings"]
    system.start_workers(settings)


@workers.command()
@click.pass_context
def restart(ctx):
    """Restart the Celery workers.

    Restarts the worker processes, which can be useful for applying
    configuration changes or resolving issues.
    """
    settings: system.Settings = ctx.obj["settings"]
    system.restart_workers(settings)


@workers.command()
@click.pass_context
def stop(ctx):
    """Stop the Celery workers.

    Manually stops the worker processes, gracefully shutting down the task
    execution environment.
    """
    settings: system.Settings = ctx.obj["settings"]
    system.stop_workers(settings)
