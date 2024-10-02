"""Module for detecting and identifying devices."""

import socket

__all__ = [
    "get_device_serial_number",
    "get_device_host_name",
    "is_rpi",
    "get_device_memory_stats",
]


def get_device_serial_number() -> str:
    """Get the serial number of the device.

    Returns
    -------
        The serial number of the device as a string.
    """
    with open("/proc/cpuinfo", "r") as f:
        for line in f:
            if line[0:6] == "Serial":
                return line[10:26]
    raise RuntimeError("Could not find serial number of the device.")


def get_device_host_name() -> str:
    """Get the hostname of the device.

    Returns
    -------
        The hostname of the device as a string.
    """
    return socket.gethostname()


def is_rpi() -> bool:
    """Check if the current device is a Raspberry Pi.

    Returns
    -------
        True if the current device is a Raspberry Pi, False otherwise.
    """
    try:
        get_device_serial_number()
        return True
    except FileNotFoundError:
        return False
    except RuntimeError:
        return False


def get_device_memory_stats() -> dict:
    """Get memory statistics of the device.

    Retruns
    -------
        A dictionary containing memory statistics.
    """
    memory_stats = shutil.disk_usage("/")
    return {
        "total": memory_stats.total,
        "used": memory_stats.used,
        "free": memory_stats.free,
    }
