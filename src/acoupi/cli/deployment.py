"""CLI commands to manage acoupi deployment."""

from typing import Dict, Literal, TypedDict

import click

from acoupi import system
from acoupi.cli.base import acoupi
from acoupi.cli.base import check as check_command
from acoupi.system.celery import CeleryState
from acoupi.system.programs import ProgramState
from acoupi.system.services import ServiceStatus
from acoupi.system.state import AcoupiStatus


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

    status = system.get_status(settings)

    click.clear()
    click.echo("Acoupi status:")

    _print_services_status(status)
    _print_celery_status(status)
    _print_program_status(status)


class Style(TypedDict):
    fg: str


def _print_services_status(status: AcoupiStatus):
    overall_status = "ok"

    if (
        status.services.acoupi == ServiceStatus.FAILED
        or status.services.beat == ServiceStatus.FAILED
    ):
        overall_status = "error"

    if (
        status.services.acoupi == ServiceStatus.UNINSTALLED
        or status.services.beat == ServiceStatus.UNINSTALLED
    ):
        overall_status = "warning"

    _print_header("System Services", overall_status)

    style = _SERVICE_STATUS_STYLES.get(status.services.acoupi, DEFAULT_STYLE)
    _print_field("acoupi", status.services.acoupi.value, style)

    style = _SERVICE_STATUS_STYLES.get(status.services.beat, DEFAULT_STYLE)
    _print_field("beat", status.services.beat.value, style)


def _print_celery_status(status: AcoupiStatus):
    _print_header("Celery", "ok")

    style = _CELERY_STATUS_STYLES.get(status.celery.state, DEFAULT_STYLE)
    _print_field("status", status.celery.state.value, style)

    if not status.celery.workers:
        return

    click.echo("  Workers:")


def _print_program_status(status: AcoupiStatus):
    overall_status = "ok"
    if status.program == ProgramState.ERROR:
        overall_status = "error"
    if status.program == ProgramState.UNHEALTHY:
        overall_status = "error"
    _print_header("Program", overall_status)

    style = _PROGRAM_STATUS_STYLES.get(status.program, DEFAULT_STYLE)
    _print_field("status", status.program.value, style)

    if status.program == ProgramState.UNHEALTHY:
        click.echo(f"\n{'':>15}Configuration errors were found")
        click.echo(f"{'':>15}Run `acoupi check` for details.")


def _print_field(field_name: str, field_value: str, style: Style) -> None:
    click.echo(
        f"  {field_name:>10} : "
        + click.style(
            f"{field_value}",
            fg=style.get("fg"),
        )
    )


def _print_header(name: str, status: Literal["ok", "warning", "error"]):
    fg = {
        "ok": "green",
        "warning": "yellow",
        "error": "red",
    }[status]
    click.echo("")
    click.echo(click.style("●", fg=fg) + click.style(f" {name}", bold=True))


DEFAULT_STYLE: Style = {"fg": "white"}

_SERVICE_STATUS_STYLES: Dict[ServiceStatus, Style] = {
    ServiceStatus.ACTIVE: {
        "fg": "green",
    },
    ServiceStatus.INACTIVE: {
        "fg": "blue",
    },
    ServiceStatus.FAILED: {
        "fg": "red",
    },
}

_CELERY_STATUS_STYLES: Dict[CeleryState, Style] = {
    CeleryState.ERROR: {
        "fg": "red",
    },
    CeleryState.AVAILABLE: {
        "fg": "green",
    },
    CeleryState.UNAVAILABLE: {
        "fg": "yellow",
    },
}

_PROGRAM_STATUS_STYLES: Dict[ProgramState, Style] = {
    ProgramState.OK: {
        "fg": "green",
    },
    ProgramState.ERROR: {
        "fg": "red",
    },
    ProgramState.UNHEALTHY: {
        "fg": "red",
    },
}
