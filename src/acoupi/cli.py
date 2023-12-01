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

    """Check the status of acoupi services."""
    click.echo("Acoupi services status are:")
    system.status_services()


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
        config = system.show_config(system.PROGRAM_CONFIG_FILE)
        click.echo("Current acoupi configuration:")
        click.echo(config)

    except Exception as e:
        click.echo(f"Error loading configuration: {e}")


@config.command()
@click.argument("config_param_name", required=False)
def get(config_param_name: str):
    """Print a configuration value."""
    if not system.is_configured():
        click.echo("Acoupi is not setup. Run `acoupi setup` first.")
        return

    # If config_paran_name is not provided, show all available configuration parameters names
    if not config_param_name:
        click.echo("Error: Missing argument 'CONFIG_PARAM_NAME'.\n")
        click.echo("Available configuration parameters:")
        config_keys = system.show_config(system.PROGRAM_CONFIG_FILE).keys()
        click.echo("\n".join(config_keys))
        return

    try:
        config_value = system.get_config_value(
            config_param_name,
            system.PROGRAM_CONFIG_FILE,
        )
        click.echo(f"{config_param_name}: {config_value}")

    except KeyError:
        click.echo(
            f"Configuration parameter '{config_param_name}' not found.\n"
        )
        click.echo("Available configuration parameters:")
        config_keys = system.show_config(system.PROGRAM_CONFIG_FILE).keys()
        click.echo("\n".join(config_keys))

    except Exception as e:
        click.echo(f"Error finding configuration parameter: {e}")


@config.command()
@click.argument("config_param_name", required=True)
@click.argument("config_param_value", required=True)
def sub(config_param_name, config_param_value):
    """Substitute a configuration value."""
    if not system.is_configured():
        click.echo("Acoupi is not setup. Run `acoupi setup` first.")
        return

    # If config_paran_name or config_param_value is not provided, show current configuration
    if not config_param_name or not config_param_value:
        click.echo(
            "Error: Missing argument 'CONFIG_PARAM_NAME' and/or 'CONFIG_PARAM_VALUE'.\n"
        )
        click.echo("Current configuration parameters are:")
        return system.show_config(system.PROGRAM_CONFIG_FILE)

    try:
        system.sub_config_value(
            config_param_name=config_param_name,
            new_config_value=config_param_value,
            config_file_path=system.PROGRAM_CONFIG_FILE,
        )
        click.echo(
            f"Configuration parameter '{config_param_name}' successfully set to '{config_param_value}'."
        )

    except Exception as e:
        click.echo(f"Error updating configuration: {e}")


if __name__ == "__main__":
    acoupi()
