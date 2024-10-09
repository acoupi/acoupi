"""CLI commands to manage acoupi deployment."""

from typing import Dict, Literal, TypedDict

import click

from acoupi import system
from acoupi.cli.base import acoupi
from acoupi.cli.base import check as check_command
from acoupi.system.celery import CeleryState, WorkerState
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
    _print_deployment_status(status)


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

    style = _SERVICE_STATUS_STYLES.get(status.services.acoupi, DEFAULT)
    _print_field("acoupi", status.services.acoupi.value, style)

    style = _SERVICE_STATUS_STYLES.get(status.services.beat, DEFAULT)
    _print_field("beat", status.services.beat.value, style)


def _print_celery_status(status: AcoupiStatus):
    _print_header("Celery", "ok")

    style = _CELERY_STATUS_STYLES.get(status.celery.state, DEFAULT)
    _print_field("status", status.celery.state.value, style)

    if not status.celery.workers:
        return

    click.echo("")
    click.secho(f"  {'workers':>10}", bold=True)

    for worker_status in status.celery.workers:
        style = _WORKER_STATUS_STYLES.get(worker_status.state, DEFAULT)
        name = worker_status.worker_name.split("@")[0]
        _print_field(name, worker_status.state.value, style)


def _print_program_status(status: AcoupiStatus):
    overall_status = "ok"
    if status.program == ProgramState.ERROR:
        overall_status = "error"
    if status.program == ProgramState.UNHEALTHY:
        overall_status = "error"
    _print_header("Program", overall_status)

    style = _PROGRAM_STATUS_STYLES.get(status.program, DEFAULT)
    _print_field("status", status.program.value, style)

    if status.program == ProgramState.UNHEALTHY:
        click.echo(f"\n{'':>15}Configuration errors were found")
        click.echo(f"{'':>15}Run `acoupi check` for details.")


def _print_deployment_status(status: AcoupiStatus):
    _print_header("Deployment", "ok" if status.deployment else "warning")

    _print_field(
        "status",
        "active" if status.deployment else "inactive",
        SUCCESS if status.deployment else INACTIVE,
    )

    if not status.deployment:
        return

    click.echo("")
    click.secho(f"  {'info':>10}", bold=True)

    _print_field(
        "started on",
        status.deployment.started_on.strftime("%A, %d. %B %Y %I:%M%p"),
        INFO,
    )

    _print_field("name", status.deployment.name, INFO)

    if status.deployment.latitude is not None:
        _print_field("latitude", str(status.deployment.latitude), INFO)

    if status.deployment.longitude is not None:
        _print_field("longitude", str(status.deployment.longitude), INFO)


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


DEFAULT: Style = {"fg": "white"}
SUCCESS: Style = {"fg": "green"}
INACTIVE: Style = {"fg": "blue"}
INFO: Style = {"fg": "cyan"}
WARNING: Style = {"fg": "yellow"}
ERROR: Style = {"fg": "red"}

_SERVICE_STATUS_STYLES: Dict[ServiceStatus, Style] = {
    ServiceStatus.ACTIVE: SUCCESS,
    ServiceStatus.INACTIVE: INACTIVE,
    ServiceStatus.FAILED: ERROR,
}

_CELERY_STATUS_STYLES: Dict[CeleryState, Style] = {
    CeleryState.ERROR: ERROR,
    CeleryState.AVAILABLE: SUCCESS,
    CeleryState.UNAVAILABLE: WARNING,
}

_PROGRAM_STATUS_STYLES: Dict[ProgramState, Style] = {
    ProgramState.OK: SUCCESS,
    ProgramState.ERROR: ERROR,
    ProgramState.UNHEALTHY: ERROR,
}

_WORKER_STATUS_STYLES: Dict[WorkerState, Style] = {
    WorkerState.OK: SUCCESS,
    WorkerState.NOTOK: ERROR,
}
