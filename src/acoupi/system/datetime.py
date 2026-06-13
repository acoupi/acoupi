"""System datetime management."""

import subprocess
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

__all__ = ["get_system_timezone", "set_system_timezone"]


def get_system_timezone() -> Optional[str]:
    """Get the current system timezone.

    Returns
    -------
    Optional[str]
        The timezone string (e.g., 'Europe/London') or None if it cannot be
        determined.
    """
    try:
        # Run timedatectl to get the current timezone
        result = subprocess.run(
            ["timedatectl", "show", "--property=Timezone", "--value"],
            capture_output=True,
            text=True,
            check=True,
        )
        tz_string = result.stdout.strip()

        if tz_string:
            return tz_string

    except subprocess.CalledProcessError:
        pass

    return None


def set_system_timezone(timezone_str: str) -> bool:
    """Set the system timezone using timedatectl.

    Parameters
    ----------
    timezone_str : str
        The timezone to set (e.g., 'America/New_York').

    Returns
    -------
    bool
        True if successful, False otherwise.
    """
    # 1. Validate that the requested timezone actually exists
    try:
        ZoneInfo(timezone_str)
    except ZoneInfoNotFoundError:
        return False

    # 2. Attempt to set it using timedatectl
    try:
        subprocess.run(
            ["sudo", "timedatectl", "set-timezone", timezone_str],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False
