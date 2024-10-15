"""CProfile templates for acoupi."""

from acoupi.tasks.cprofile.cprofile_detection import (
    cprofile_create_detection_task,
)
from acoupi.tasks.cprofile.cprofile_management import (
    cprofile_create_management_task,
)
from acoupi.tasks.cprofile.cprofile_messaging import (
    cprofile_create_messaging_task,
)

__all__ = [
    "cprofile_create_detection_task",
    "cprofile_create_management_task",
    "cprofile_create_messaging_task",
]
