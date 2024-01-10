"""Functions that manage Acoupi system.

This module contains utility functions for acoupi programs
such as loading programs and getting celery apps from programs.
"""

from acoupi.system.apps import get_celery_app
from acoupi.system.configs import (
    get_config_value,
    is_configured,
    load_config,
    show_config,
    sub_config_value,
    write_config,
)
from acoupi.system.constants import Settings
from acoupi.system.deployments import get_current_deployment
from acoupi.system.parsers import parse_config_from_args
from acoupi.system.programs import (
    load_program,
    load_program_class,
    setup_program,
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

__all__ = [
    "Settings",
    "disable_services",
    "enable_services",
    "get_celery_app",
    "get_config_value",
    "get_current_deployment",
    "is_configured",
    "load_config",
    "load_program",
    "load_program_class",
    "parse_config_from_args",
    "services_are_installed",
    "setup_program",
    "show_config",
    "start_services",
    "status_services",
    "stop_services",
    "sub_config_value",
    "write_config",
    "write_program_file",
]
