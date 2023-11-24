"""CLI for acoupi."""
from typing import List

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
@click.option("--program", type=str, default="acoupi.programs.custom.test")
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def setup(program: str, args: List[str]):
    """Setup acoupi."""
    try:
        system.setup_program(program, args, prompt=True)

    except exceptions.ProgramNotFoundError as err:
        # TODO: Improve this messages
        click.echo(f"program {err.program} not found")
        raise click.Abort() from err

    except exceptions.InvalidProgramError as err:
        click.echo("program is invalid")
        raise click.Abort() from err

    except ValueError as err:
        click.echo("program not found")
        raise click.Abort() from err


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


@acoupi.command()
def status():
    """Check the status of acoupi services."""
    if not system.is_configured():
        click.echo("Acoupi is not setup. Run `acoupi setup` first.")
        return

    try:
        # Check if acoupi services are enabled.
        if system.enable_services():
            click.echo("Acoupi services are ON.")

        # Check if acoupi services are disabled.
        elif system.disable_services():
            click.echo("Acoupi services are OFF.")

    except Exception as e:
        click.echo(f"Error checking acoupi status: {e}")


@acoupi.group()
def config():
    """Manage acoupi configuration."""
    if not system.is_configured():
        click.echo("Acoupi is not setup. Run `acoupi setup` first.")
        return


@config.command()
def show():
    """Show the entire configuration of acoupi."""
    if not system.is_configured():
        click.echo("Acoupi is not setup. Run `acoupi setup` first.")
        return

    try:
        config = system.load_config(
            system.PROGRAM_CONFIG_FILE, system.CeleryConfig
        )
        click.echo("Current acoupi Configuration:")
        click.echo(config.json(inedent=2))

    except Exception as e:
        click.echo(f"Error loading configuration: {e}")


@config.command()
@click.argument("config_param_name")
def get(config_param_name: str):
    """Print a configuration value."""
    if not system.is_configured():
        click.echo("Acoupi is not setup. Run `acoupi setup` first.")
        return

    try:
        config = system.load_config(
            system.PROGRAM_CONFIG_FILE, system.CeleryConfig
        )

        # Check if the parameter exists in the configuration
        if hasattr(config, config_param_name):
            config_param_value = getattr(config, config_param_name)
            click.echo(f"{config_param_name}: {config_param_value}")
        else:
            click.echo(
                f"Configuration parameter '{config_param_name}' not found."
            )

    except Exception as e:
        click.echo(f"Error loading configuration: {e}")


@config.command()
@click.argument("config_param_name")
@click.argument("config_param_value")
def sub(config_param_name, config_param_value):
    """Substitute a configuration value."""
    if not system.is_configured():
        click.echo("Acoupi is not setup. Run `acoupi setup` first.")
        return

    try:
        config = system.load_config(
            system.PROGRAM_CONFIG_FILE, system.CeleryConfig
        )

        # Check if the parameter exists in the configuration
        if hasattr(config, config_param_name):
            # Update the configuration with the new value
            setattr(config, config_param_name, config_param_value)
            # Write the updated configuration back to the config file
            system.write_config(config, system.PROGRAM_CONFIG_FILE)
            click.echo(
                f"Configuration parameter '{config_param_name}' set to '{config_param_value}'."
            )
        else:
            click.echo(
                f"Configuration parameter '{config_param_name}' not found."
            )

    except Exception as e:
        click.echo(f"Error loading or updating configuration: {e}")


if __name__ == "__main__":
    acoupi()
