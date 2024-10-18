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
    """Manage acoupi tasks.

    Provides commands to list, run, and profile tasks within
    your configured acoupi program.
    """
    settings = ctx.obj["settings"]
    if not system.is_configured(settings):
        click.echo("Acoupi is not setup. Run `acoupi setup` first.")
        return


@task.command()
@click.pass_context
def list(ctx):
    """List all available tasks in the current acoupi program."""
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
    """Run a specified task.

    Parameters
    ----------
    task_name : str
        The name of the task to run.
    """
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
@click.option(
    "--output",
    type=Path,
    help="Path to save profiling output.",
)
@click.option(
    "--quiet",
    type=bool,
    default=False,
    help="Suppress printing profiling output to the console.",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="WARNING",
    help="Set the logging level.",
)
@click.pass_context
def profile(
    ctx,
    task_name: str,
    output: Optional[Path],
    quiet: bool,
    log_level: str,
):
    """Profile a specified task.

    Parameters
    ----------
    task_name : str
        The name of the task to profile.
    """
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

    stats = system.profile_task(program, task_name)

    if output:
        stats.dump_stats(output)
