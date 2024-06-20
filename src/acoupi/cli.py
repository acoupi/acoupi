"""CLI for acoupi."""

import json
from typing import List

import click

from acoupi import system
from acoupi.system import Settings, exceptions

__all__ = [
    "acoupi",
    "setup",
    "start",
    "stop",
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
@click.option("--program", type=str, default="acoupi.programs.custom.test")
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
@click.option(
    "--name",
    type=str,
    prompt="Enter the name of the deployment",
)
@click.option(
    "--latitude",
    type=float,
    prompt="Enter the latitude of the deployment",
    help="Latitude of the deployment",
)
@click.option(
    "--longitude",
    type=float,
    prompt="Enter the longitude of the deployment",
)
@click.pass_context
def start(ctx, name, latitude, longitude):
    """Start acoupi."""
    settings = ctx.obj["settings"]

    if not system.is_configured(settings):
        click.echo("Acoupi is not setup. Run `acoupi setup` first.")
        return

    click.secho("Starting acoupi...", fg="green")
    system.start_program(settings, name, latitude, longitude)
    click.secho("Acoupi started.", fg="green")


@acoupi.command()
@click.pass_context
def stop(ctx):
    """Stop acoupi."""
    settings = ctx.obj["settings"]

    if not system.is_configured(settings):
        click.echo("Acoupi is not setup. Run `acoupi setup` first.")
        return

    click.secho("Stopping acoupi...", fg="green")
    system.stop_program(settings)
    click.secho("Acoupi stopped.", fg="green")


@acoupi.command()
@click.pass_context
def status(ctx):
    """Check the status of acoupi services."""
    settings = ctx.obj["settings"]
    if not system.is_configured(settings):
        click.echo("Acoupi is not setup. Run `acoupi setup` first.")
        return

    """Check the status of acoupi services."""
    click.echo("Acoupi services status are:")
    system.status_services(settings)


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
def show(ctx):
    """Show the entire configuration of acoupi."""
    settings = ctx.obj["settings"]

    if not system.is_configured(settings):
        click.echo("Acoupi is not setup. Run `acoupi setup` first.")
        return

    try:
        config = system.show_config(settings)
        formatted_config = json.dumps(config, indent=4)
        click.echo("Current acoupi configuration:")
        click.echo(formatted_config)

    except Exception as e:
        click.echo(f"Error loading configuration: {e}")


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
        config_keys = system.show_config(settings).keys()
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
        config_keys = system.show_config(settings).keys()
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
        current_config = json.dumps(system.show_config(settings), indent=4)
        click.echo(f"Current configuration parameters are: {current_config}")
        return

    try:
        # update the system with the new value
        system.sub_config_value(
            settings, config_param_name, config_param_value
        )
        click.echo(
            f"Configuration parameter '{config_param_name}' successfully set to '{config_param_value}'."
        )

    except Exception as e:
        click.echo(f"Error updating configuration: {e}")


@acoupi.command()
@click.pass_context
def check(ctx):
    """Run the health checks of the current program and configurations."""
    settings = ctx.obj["settings"]

    if not system.is_configured(settings):
        click.echo("Acoupi is not setup. Run `acoupi setup` first.")
        return

    click.secho("Running health checks...", fg="green")
    program = system.load_program(settings)
    try:
        program.check(program.config)
    except exceptions.HealthCheckError as err:
        click.secho(f"Error: {err}", fg="red")
        raise click.Abort() from err
    click.secho("Health checks passed.", fg="green")


if __name__ == "__main__":
    acoupi()
