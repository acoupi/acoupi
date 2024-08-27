"""Base command line interface for acoupi."""

from typing import List

import click

from acoupi import system
from acoupi.system import Settings, exceptions

__all__ = [
    "acoupi",
]


@click.group()
@click.pass_context
def acoupi(ctx):
    """Welcome to acoupi.

    This is the main command line interface for acoupi and allows you to
    setup and run acoupi programs.

    To get started run `acoupi setup` to setup your first program.
    """
    ctx.ensure_object(dict)

    if "settings" not in ctx.obj:
        ctx.obj["settings"] = Settings()


@acoupi.command(
    context_settings=dict(
        allow_extra_args=True,
        ignore_unknown_options=True,
    )
)
@click.option("--program", type=str, default="acoupi.programs.test")
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def setup(ctx, program: str, args: List[str]):
    """Set up acoupi."""
    click.echo(
        "Collecting program files. It will take a minute or so, be patient..."
    )

    settings = ctx.obj["settings"]

    try:
        system.setup_program(settings, program, args=args, prompt=True)

    except exceptions.ProgramNotFoundError as err:
        # TODO: Improve this messages
        click.echo(f"program {err.program} not found")
        raise click.Abort() from err

    except exceptions.InvalidProgramError as err:
        click.echo("program is invalid")
        raise click.Abort() from err

    except exceptions.ParameterError as err:
        click.secho(
            "Setup failed. The was an error configuring the parameter "
            f"'{err.value}': {err.message}.",
            fg="red",
        )
        if err.help:
            click.secho(f"Help: {err.help}", fg="yellow")
        raise click.Abort() from err

    except ValueError as err:
        click.echo("program not found")
        raise err


@acoupi.command()
@click.pass_context
def check(ctx):
    """Run the health checks of the current program and configurations."""
    settings = ctx.obj["settings"]

    if not system.is_configured(settings):
        click.echo("Acoupi is not setup. Run `acoupi setup` first.")
        raise click.Abort()

    click.secho("Running health checks...", fg="green")
    program = system.load_program(settings)

    try:
        program.check(program.config)
    except exceptions.HealthCheckError as err:
        click.secho(f"Error: {err}", fg="red")
        raise click.Abort() from err

    click.secho("Health checks passed.", fg="green")


@acoupi.command()
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def celery(ctx, args: List[str]):
    """Run a celery command."""
    settings: Settings = ctx.obj["settings"]

    if not system.is_configured(settings):
        click.echo("Acoupi is not setup. Run `acoupi setup` first.")
        raise click.Abort()

    system.run_celery_command(settings, args)
