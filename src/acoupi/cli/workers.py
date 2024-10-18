import click

from acoupi import system
from acoupi.cli.base import acoupi

__all__ = [
    "workers",
]


@acoupi.group()
@click.pass_context
def workers(ctx):
    """Manage acoupi tasks."""
    settings = ctx.obj["settings"]
    if not system.is_configured(settings):
        raise click.UsageError(
            "Acoupi is not setup. Run `acoupi setup` first."
        )


@workers.command()
@click.pass_context
def start(ctx):
    """Run a celery command."""
    settings: system.Settings = ctx.obj["settings"]
    system.start_workers(settings)


@workers.command()
@click.pass_context
def restart(ctx):
    """Run a celery command."""
    settings: system.Settings = ctx.obj["settings"]
    system.restart_workers(settings)


@workers.command()
@click.pass_context
def stop(ctx):
    """Run a celery command."""
    settings: system.Settings = ctx.obj["settings"]
    system.stop_workers(settings)
