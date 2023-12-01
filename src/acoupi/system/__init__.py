"""Functions that manage Acoupi system.

This module contains utility functions for acoupi programs
such as loading programs and getting celery apps from programs.
"""

from acoupi.system.apps import get_celery_app
from acoupi.system.configs import (
    write_config,
    load_config,
    is_configured,
    show_config,
    get_config_value,
    sub_config_value,
)
from acoupi.system.constants import (
    ACOUPI_HOME,
    PROGRAM_CONFIG_FILE,
    PROGRAM_PATH,
)
from acoupi.system.deployments import get_current_deployment
from acoupi.system.parsers import parse_config_from_args
from acoupi.system.programs import (
    load_program,
    setup_program,
    write_program_file,
)
from acoupi.system.services import (
    disable_services,
    enable_services,
    start_services,
    stop_services,
    services_are_installed,
    status_services,
)

__all__ = [
    "ACOUPI_HOME",
    "PROGRAM_CONFIG_FILE",
    "PROGRAM_PATH",
    "disable_services",
    "enable_services",
    "get_celery_app",
    "get_current_deployment",
    "get_config_value",
    "is_configured",
    "load_config",
    "load_program",
    "parse_config_from_args",
    "services_are_installed",
    "setup_program",
    "show_config",
    "start_services",
    "stop_services",
    "status_services",
    "sub_config_value",
    "write_config",
    "write_program_file",
]
