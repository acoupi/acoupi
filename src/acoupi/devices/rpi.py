"""Module for detecting and identifying devices."""

import socket

__all__ = [
    "get_rpi_serial_number",
    "get_rpi_host_name",
    "is_rpi",
]


def get_rpi_serial_number() -> str:
    """Get the serial number of the Raspberry Pi.

    Returns
    -------
        The serial number of the Raspberry Pi as a string.
    """
    with open("/proc/cpuinfo", "r") as f:
        for line in f:
            if line[0:6] == "Serial":
                return line[10:26]
    raise RuntimeError("Could not find serial number of Raspberry Pi")


def get_rpi_host_name() -> str:
    """Get the hostname of the Raspberry Pi.

    Returns
    -------
        The hostname of the Raspberry Pi as a string.
    """
    return socket.gethostname()


def is_rpi() -> bool:
    """Check if the current device is a Raspberry Pi.

    Returns
    -------
        True if the current device is a Raspberry Pi, False otherwise.
    """
    try:
        get_rpi_serial_number()
        return True
    except FileNotFoundError:
        return False
    except RuntimeError:
        return False
