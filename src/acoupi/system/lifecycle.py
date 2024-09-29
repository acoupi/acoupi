"""System functions for managing Acoupi programs."""

from typing import List, Optional

from acoupi.system import programs, services
from acoupi.system.config import parse_config_from_args, write_config
from acoupi.system.constants import CeleryConfig, Settings
from acoupi.system.deployments import end_deployment, start_deployment
from acoupi.system.scripts import write_scripts

__all__ = [
    "setup_program",
    "start_program",
    "stop_program",
]


def start_program(
    settings: Settings,
    name: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> None:
    deployment = start_deployment(settings, name, latitude, longitude)

    try:
        program = programs.load_program(settings)
        program.on_start(deployment)
        services.enable_services(settings)
        services.start_services(settings)
    except Exception as error:
        settings.deployment_file.unlink()
        raise error


def stop_program(settings: Settings) -> None:
    services.stop_services(settings)
    services.disable_services(settings)
    deployment = end_deployment(settings)
    program = programs.load_program(settings)
    program.on_end(deployment)


def setup_program(
    settings: Settings,
    program_name: str,
    args: Optional[List[str]] = None,
    prompt: bool = False,
) -> None:
    """Set up an Acoupi Program."""
    if args is None:
        args = []

    # Load acoupi program class from specified module
    program_class = programs.load_program_class(program_name)

    # Write the celery app program file
    programs.write_program_file(program_name, settings)

    # Write the name of the program to a file
    if not settings.program_name_file.parent.exists():
        settings.program_name_file.parent.mkdir(parents=True)
    settings.program_name_file.write_text(program_name)

    # Get program config schema
    config_schema = program_class.get_config_schema()
    if config_schema is not None:
        # Generate program configuration from arguments
        config = parse_config_from_args(config_schema, args, prompt=prompt)

        # Write program configuration to file
        write_config(config, settings.program_config_file)

    # Generate scripts for starting, stopping, and restarting the program
    worker_config = program_class.get_worker_config()
    write_scripts(worker_config, settings)

    # Generate celery configuration from arguments and write to file
    celery_config = parse_config_from_args(CeleryConfig, args, prompt=False)
    write_config(celery_config, settings.celery_config_file)

    # Make sure run and log directories exist
    settings.run_dir.mkdir(parents=True, exist_ok=True)
    settings.log_dir.mkdir(parents=True, exist_ok=True)

    # Install systemd services for acoupi
    services.install_services(settings)
