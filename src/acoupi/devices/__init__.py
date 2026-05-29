"""Acoupi devices module.

This module provides functions to retrieve information about the device
on which Acoupi is running. This includes identifying the device type
(currently supports Raspberry Pi), and obtaining unique identifiers
like serial numbers and hostnames.
"""

import uuid
from functools import cache

from acoupi.data import DeviceInfo
from acoupi.devices.rpi import get_rpi_host_name, get_rpi_serial_number, is_rpi


def get_device_id() -> str:
    """Get a unique identifier for the current device.

    This function returns a device-specific identifier.

    - If the device is a Raspberry Pi, the serial number is returned.
    - Otherwise, the MAC address is used as the identifier,
      retrieved via `uuid.getnode()`.

    Returns
    -------
    str
        The device ID.

    Notes
    -----
        For potential limitations of using MAC addresses for identification,
        refer to the [`uuid.getnode()`][uuid.getnode] documentation.
    """
    if is_rpi():
        return get_rpi_serial_number()

    return str(uuid.getnode())


@cache
def get_device_info() -> DeviceInfo:
    """Get cached runtime information about the current device.

    Returns
    -------
    DeviceInfo
        Device information for the current process. If the device identifier
        cannot be resolved, the returned object contains an empty ``id``.
    """
    try:
        return DeviceInfo(id=get_device_id())
    except Exception:
        return DeviceInfo(id="")


__all__ = [
    "get_rpi_serial_number",
    "get_rpi_host_name",
    "get_device_id",
    "get_device_info",
    "is_rpi",
]
