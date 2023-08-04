"""Functions that manage Acoupi system.

This module contains utility functions for acoupi programs
such as loading programs and getting celery apps from programs.
"""

from acoupi.system.apps import get_celery_app
from acoupi.system.configs import is_configured, write_config
from acoupi.system.constants import ACOUPI_HOME, PROGRAM_CONFIG_FILE, PROGRAM_PATH
from acoupi.system.deployments import get_current_deployment
from acoupi.system.programs import (
    load_program,
    setup_program,
    write_program_file,
)

__all__ = [
    "ACOUPI_HOME",
    "PROGRAM_CONFIG_FILE",
    "PROGRAM_PATH",
    "get_celery_app",
    "get_current_deployment",
    "is_configured",
    "load_program",
    "write_config",
    "write_program_file",
    "setup_program",
]
