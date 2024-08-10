"""CLI commands to manage acoupi configuration."""

import json

import click
import pygments
from pygments.formatters import TerminalFormatter
from pygments.lexers import JsonLexer

from acoupi import system
from acoupi.cli.base import acoupi
from acoupi.system import Settings, exceptions

__all__ = [
    "config",
]


@acoupi.group()
@click.pass_context
def config(ctx):
    """Manage acoupi configuration."""
    settings = ctx.obj["settings"]
    if not system.is_configured(settings):
        click.echo("Acoupi is not setup. Run `acoupi setup` first.")
        return


@config.command()
@click.pass_context
@click.option(
    "--color/--no-color",
    default=True,
    help="Enable or disable color output.",
)
@click.option(
    "--indent",
    "-i",
    type=int,
    default=2,
    help="Indentation level.",
)
def show(ctx, color: bool, indent: int):
    """Show the entire configuration of acoupi."""
    settings: Settings = ctx.obj["settings"]
    try:
        program = system.load_program(settings)
    except exceptions.ProgramNotFoundError as err:
        click.secho(
            f"We couldn't find the program\n\nError: {err.program}",
            fg="red",
        )
        return
    except exceptions.InvalidProgramError as err:
        click.secho(
            f"The program is invalid\n\nError: {err.program}",
            fg="red",
        )
        return

    schema = program.get_config_schema()

    try:
        config = system.load_config(
            settings.program_config_file,
            schema,
        )
    except exceptions.ConfigurationError as err:
        click.secho(
            f"The configuration file is invalid\n\nError: {err}",
            fg="red",
        )
        return

    output = config.model_dump_json(indent=indent)
    if color:
        output = pygments.highlight(
            output,
            JsonLexer(),
            TerminalFormatter(),
        )

    click.echo("Current acoupi configuration:\n")
    click.echo(output)


@config.command()
@click.argument("config_param_name", required=False)
@click.pass_context
def get(ctx, config_param_name: str):
    """Print a configuration value."""
    settings = ctx.obj["settings"]

    if not system.is_configured(settings):
        click.echo("Acoupi is not setup. Run `acoupi setup` first.")
        return

    # If config_paran_name is not provided, show all available configuration parameters names
    if not config_param_name:
        click.echo("Error: Missing argument 'CONFIG_PARAM_NAME'.\n")
        click.echo("Available configuration parameters:")
        config_keys = system.get_config(settings).keys()
        click.echo("\n".join(config_keys))
        return

    try:
        config_value = system.get_config_value(config_param_name, settings)
        click.echo(f"{config_param_name}: {config_value}")

    except KeyError:
        click.echo(
            f"Configuration parameter '{config_param_name}' not found.\n"
        )
        click.echo("Available configuration parameters:")
        config_keys = system.get_config(settings).keys()
        click.echo("\n".join(config_keys))

    except Exception as e:
        click.echo(f"Error finding configuration parameter: {e}")


@config.command()
@click.argument("config_param_name", required=True)
@click.argument("config_param_value", required=True)
@click.pass_context
def sub(ctx, config_param_name, config_param_value):
    """Substitute a configuration value."""
    settings = ctx.obj["settings"]

    if not system.is_configured(settings):
        click.echo("Acoupi is not setup. Run `acoupi setup` first.")
        return

    # If config_paran_name or config_param_value is not provided, show current
    # configuration
    if not config_param_name or not config_param_value:
        click.echo(
            "Error: Missing argument 'CONFIG_PARAM_NAME' and/or 'CONFIG_PARAM_VALUE'.\n"
        )
        current_config = json.dumps(system.get_config(settings), indent=4)
        click.echo(f"Current configuration parameters are: {current_config}")
        return

    try:
        # update the system with the new value
        system.set_config_value(
            settings, config_param_name, config_param_value
        )
        click.echo(
            f"Configuration parameter '{config_param_name}' successfully set to '{config_param_value}'."
        )

    except Exception as e:
        click.echo(f"Error updating configuration: {e}")
