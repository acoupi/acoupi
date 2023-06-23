"""CLI for acoupi."""
import os
import signal
import subprocess

import click

from acoupi import system


@click.group()
def acoupi():
    """Acoupi CLI."""


@acoupi.command(
    context_settings=dict(
        allow_extra_args=True,
        ignore_unknown_options=True,
    )
)
@click.option("--program", type=str, default="sample_program")
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def setup(program: str, args: list[str]):
    """Setup acoupi."""
    program_class = system.load_program(program)

    if program_class is None:
        click.echo("program not found")
        return

    config_schema = program_class.get_config_schema()
    config = config_schema.from_args(args)
    system.write_config(config)
    system.write_program_file(program)


@acoupi.command()
def start():
    """Start acoupi."""
    if not system.is_configured():
        click.echo("Acoupi is not setup. Run `acoupi setup` first.")
        return

    commands = [
            "celery",
            "--app",
            "app",
            "--workdir",
            str(system.PROGRAM_PATH.parent),
            "worker",
            "--pidfile=worker.pid",
            "--logfile=worker.log",
            "--detach",
        ]

    subprocess.run(
        commands,
        start_new_session=True,
    )

    subprocess.Popen(
        [
            "celery",
            "-A",
            "app",
            "--workdir",
            str(system.PROGRAM_PATH.parent),
            "beat",
            "--pidfile=beat.pid",
            "--logfile=beat.log",
            "--loglevel=INFO",
        ],
        start_new_session=True,
    )


@acoupi.command()
def stop():
    """Stop acoupi."""
    subprocess.run(
        [
            "celery",
            "-A",
            "app",
            "--workdir",
            str(system.PROGRAM_PATH.parent),
            "multi",
            "stop",
            "w1",
            "w2",
            "--pidfile=%n.pid",
            "--logfile=%n%I.log",
            "--loglevel=INFO",
            "--detach",
        ],
        start_new_session=True,
    )

    beat_pid_file = system.ACOUPI_HOME / "beat.pid"
    beat_pid = (beat_pid_file).read_text()
    os.kill(int(beat_pid), signal.SIGTERM)
    beat_pid_file.unlink()


if __name__ == "__main__":
    acoupi()
