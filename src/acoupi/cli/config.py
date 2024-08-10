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
    """Manage the acoupi configuration.

    This command group provides subcommands to view and modify the acoupi
    configuration settings.

    Before using any subcommands, ensure that acoupi is properly set up by
    running `acoupi setup`.
    """
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
    help=(
        "Retrieve a specific field or nested field from the configuration "
        "using dot notation (e.g., 'section.subsection.value'). If not "
        "provided, the entire configuration is displayed."
    ),
)
@click.option(
    "--color/--no-color",
    default=True,
    help=(
        "Enable or disable syntax highlighting for improved readability. "
        "Default is enabled."
    ),
)
@click.option(
    "--indent",
    "-i",
    type=int,
    default=2,
    help="Set the indentation level for the output JSON. Default is 2 spaces.",
)
def get_config_field(ctx, field: str, color: bool, indent: int):
    """Display the full (or a specific field of the) acoupi configuration.

    This command allows you to view the current configuration settings for
    acoupi. You can either retrieve the entire configuration or a specific
    field or nested field within the configuration.

    Examples
    --------
    To display the entire configuration:

        acoupi config get

    To display the value of the `username` field:

        acoupi config get --field username

    To display the value of the nested field `server.port`:

        acoupi config get --field server.port

    To display the configuration without color highlighting:

        acoupi config get --no-color
    """
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
@click.argument("value", required=True, type=str)
@click.option(
    "--field",
    type=str,
    default="",
    help=(
        "Set a specific field of the configuration using dot notation "
        "(e.g., 'section.subsection.value'). "
        "If not provided, the entire configuration is modified."
    ),
)
@click.pass_context
def set_field(ctx, field: str, value: str):
    """Set a specific field or the entire acoupi configuration to a new VALUE.

    This command allows you to update a configuration value by specifying its
    new value. You can:

    * Modify the entire configuration (if `--field` is not provided)

    * Modify a specific field

    * Modify nested fields using dot notation (e.g., 'section.subsection.value')

    Note: Any configuration changes provided are validated against the original
    configuration schema to ensure data integrity.

    Examples
    --------
    To change the `username` to "new_user":

        acoupi config set username new_user

    To change the nested field `server.port` to 8080:

        acoupi config set server.port 8080

    To replace the entire configuration with a new one (assuming
    'new_config.json' contains valid JSON):

        acoupi config set "$(cat new_config.json)"
    """
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
