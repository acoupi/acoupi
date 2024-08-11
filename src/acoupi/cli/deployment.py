"""CLI commands to manage acoupi deployment."""

import click

from acoupi import system
from acoupi.cli.base import acoupi
from acoupi.cli.base import check as check_command


@acoupi.group()
@click.pass_context
def deployment(ctx):
    """Manage acoupi deployments."""
    settings = ctx.obj["settings"]
    if not system.is_configured(settings):
        click.echo("Acoupi is not setup. Run `acoupi setup` first.")
        return


@deployment.command()
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
@click.option(
    "--check/--no-check",
    default=True,
    help="Whether to run the health checks before starting the deployment.",
)
@click.pass_context
def start(ctx, name, latitude, longitude, check):
    """Start acoupi."""
    settings = ctx.obj["settings"]

    if check:
        ctx.invoke(check_command)

    click.secho("Starting acoupi...", fg="green")
    system.start_program(settings, name, latitude, longitude)
    click.secho("Acoupi started.", fg="green")


@deployment.command()
@click.pass_context
def stop(ctx):
    """Stop acoupi."""
    settings = ctx.obj["settings"]
    click.secho("Stopping acoupi...", fg="green")
    system.stop_program(settings)
    click.secho("Acoupi stopped.", fg="green")


@deployment.command()
@click.pass_context
def status(ctx):
    """Check the status of acoupi services."""
    settings = ctx.obj["settings"]
    click.echo("Acoupi services status are:")
    system.status_services(settings)
