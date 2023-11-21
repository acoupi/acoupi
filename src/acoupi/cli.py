"""CLI for acoupi."""
import click

from acoupi import system
from acoupi.system import exceptions

__all__ = [
    "acoupi",
    "setup",
    "start",
    "stop",
]


@click.group()
def acoupi():
    """Welcome to acoupi.

    This is the main command line interface for acoupi and allows you to
    setup and run acoupi programs.

    To get started run `acoupi setup` to setup your first program.
    """


@acoupi.command(
    context_settings=dict(
        allow_extra_args=True,
        ignore_unknown_options=True,
    )
)
@click.option("--program", type=str, default="sample_program")
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def setup(program: str, args: list[str]):
    """Setup acoupi."""
    try:
        system.setup_program(program, args, prompt=True)

    except exceptions.ProgramNotFoundError as err:
        # TODO: Improve this messages
        click.echo(f"program {err.program} not found")

    except exceptions.InvalidProgramError:
        click.echo("program is invalid")

    except ValueError:
        click.echo("program not found")


@acoupi.command()
def start():
    """Start acoupi."""
    if not system.is_configured():
        click.echo("Acoupi is not setup. Run `acoupi setup` first.")
        return

    system.enable_services()
    system.start_services()


@acoupi.command()
def stop():
    """Stop acoupi."""
    system.stop_services()
    system.disable_services()


@acoupi.group()
def config():
    """Manage acoupi configuration."""
    if not system.is_configured():
        click.echo("Acoupi is not setup. Run `acoupi setup` first.")
        return


@config.command()
def show():
    """Show acoupi all of the configuration."""
    # TODO: implement this


@config.command()
def get():
    """Print a configuration value."""


@config.command()
def set():
    """Set a configuration value."""


if __name__ == "__main__":
    acoupi()
