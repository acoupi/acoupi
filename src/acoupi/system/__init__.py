"""Functions that manage Acoupi system.

This module contains utility functions for acoupi programs
such as loading programs and getting celery apps from programs.
"""

from acoupi.system.apps import get_celery_app
from acoupi.system.configs import is_configured, write_config
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
)

__all__ = [
    "ACOUPI_HOME",
    "PROGRAM_CONFIG_FILE",
    "PROGRAM_PATH",
    "disable_services",
    "enable_services",
    "get_celery_app",
    "get_current_deployment",
    "is_configured",
    "load_program",
    "parse_config_from_args",
    "setup_program",
    "start_services",
    "stop_services",
    "write_config",
    "write_program_file",
]
