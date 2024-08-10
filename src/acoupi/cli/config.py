"""CLI commands to manage acoupi configuration."""

import click
import pygments
from pygments.formatters import TerminalFormatter
from pygments.lexers import JsonLexer

from acoupi import system
from acoupi.cli.base import acoupi
from acoupi.system import exceptions

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
        raise click.Abort()

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
        raise click.Abort() from err

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
        raise click.Abort() from err

    ctx.obj["config"] = config


@config.command("get")
@click.pass_context
@click.option(
    "--field",
    type=str,
    help="Show a specific field from the configuration.",
)
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
def get_config_field(ctx, field: str, color: bool, indent: int):
    """Show the entire configuration of acoupi."""
    config = ctx.obj["config"]

    if field:
        config = system.get_config_field(config, field)

    output = system.dump_config(config, indent=indent)

    if color:
        output = pygments.highlight(
            output,
            JsonLexer(),
            TerminalFormatter(),
        )

    click.echo(output)


@config.command("set")
@click.argument("field", type=str)
@click.argument("value", required=True, type=str)
@click.pass_context
def set_field(ctx, field: str, value: str):
    """Set a configuration value."""
    config = ctx.obj["config"]
    settings = ctx.obj["settings"]

    try:
        new_config = system.set_config_field(config, field, value)
    except (
        IndexError,
        ValueError,
        AttributeError,
    ) as err:
        raise click.UsageError(
            f"Invalid field or value. \n"
            f"{click.style(err, fg='red', bold=True)}",
            ctx=ctx,
        ) from err

    system.write_config(new_config, settings.program_config_file)
