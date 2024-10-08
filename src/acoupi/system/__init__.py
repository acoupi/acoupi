"""Functions that manage Acoupi system.

This module contains utility functions for acoupi programs
such as loading programs and getting celery apps from programs.
"""

from acoupi.system.apps import get_celery_app
from acoupi.system.celery import run_celery_command
from acoupi.system.config import (
    dump_config,
    get_config_field,
    load_config,
    parse_config_from_args,
    set_config_field,
    write_config,
)
from acoupi.system.constants import Settings
from acoupi.system.deployments import (
    end_deployment,
    get_current_deployment,
    start_deployment,
)
from acoupi.system.files import (
    delete_recording,
    get_temp_file_id,
    get_temp_files,
    move_recording,
)
from acoupi.system.lifecycle import setup_program, start_program, stop_program
from acoupi.system.programs import (
    load_config_schema,
    load_program,
    load_program_class,
    write_program_file,
)
from acoupi.system.services import (
    disable_services,
    enable_services,
    services_are_installed,
    start_services,
    status_services,
    stop_services,
)
from acoupi.system.state import is_configured

__all__ = [
    "Settings",
    "delete_recording",
    "disable_services",
    "dump_config",
    "enable_services",
    "end_deployment",
    "get_celery_app",
    "get_config_field",
    "get_current_deployment",
    "get_temp_file_id",
    "get_temp_files",
    "is_configured",
    "load_config",
    "load_program",
    "load_program_class",
    "load_config_schema",
    "move_recording",
    "parse_config_from_args",
    "run_celery_command",
    "services_are_installed",
    "set_config_field",
    "setup_program",
    "start_deployment",
    "start_program",
    "start_services",
    "status_services",
    "stop_program",
    "stop_services",
    "write_config",
    "write_program_file",
]
