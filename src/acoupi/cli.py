"""CLI for acoupi."""
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
    try:
        system.setup_program(program, args, prompt=True)

    except ValueError:
        click.echo("program not found")


@acoupi.command()
def start():
    """Start acoupi."""
    if not system.is_configured():
        click.echo("Acoupi is not setup. Run `acoupi setup` first.")
        return

    system.enable_services()
    system.start_services()


@acoupi.command()
def stop():
    """Stop acoupi."""
    system.stop_services()
    system.disable_services()


if __name__ == "__main__":
    acoupi()
