import logging
from pathlib import Path
from typing import Optional

import click

from acoupi import system
from acoupi.cli.base import acoupi

__all__ = [
    "task",
]


@acoupi.group()
@click.pass_context
def task(ctx):
    """Manage acoupi tasks."""
    settings = ctx.obj["settings"]
    if not system.is_configured(settings):
        click.echo("Acoupi is not setup. Run `acoupi setup` first.")
        return


@task.command()
@click.pass_context
def list(ctx):
    program = system.load_program(ctx.obj["settings"])
    task_list = system.get_task_list(program)

    click.echo(
        "Program "
        + click.style(type(program).__name__, fg="green", bold=True)
        + " tasks:\n"
    )

    for task in task_list:
        click.secho(f"  • {task}", bold=True)


@task.command()
@click.argument("task_name", type=str)
@click.pass_context
def run(ctx, task_name: str):
    program = system.load_program(ctx.obj["settings"])
    task_list = system.get_task_list(program)

    if task_name not in task_list:
        raise click.UsageError(
            click.style("Task ", fg="red")
            + click.style(task_name, fg="red", bold=True)
            + click.style(" not found.", fg="red")
        )

    click.echo(f"Running task {click.style(task_name, fg='green')}")
    system.run_task(program, task_name)


@task.command()
@click.argument("task_name", type=str)
@click.option("--output", type=Path)
@click.option(
    "--quiet",
    type=bool,
    default=False,
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="WARNING",
)
@click.pass_context
def profile(
    ctx,
    task_name: str,
    output: Optional[Path],
    quiet: bool,
    log_level: str,
):
    program = system.load_program(ctx.obj["settings"])
    task_list = system.get_task_list(program)

    if not quiet:
        logging.basicConfig(level=log_level)

    if task_name not in task_list:
        raise click.UsageError(
            click.style("Task ", fg="red")
            + click.style(task_name, fg="red", bold=True)
            + click.style(" not found.", fg="red")
        )

    if not quiet:
        click.echo(f"Profiling task {click.style(task_name, fg='green')}")
    system.profile_task(program, task_name, output=output)
