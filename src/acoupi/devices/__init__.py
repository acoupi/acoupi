import uuid

from acoupi.devices.rpi import get_rpi_host_name, get_rpi_serial_number, is_rpi


def get_device_id() -> str:
    if is_rpi():
        return get_rpi_serial_number()

    return str(uuid.getnode())


__all__ = [
    "get_rpi_serial_number",
    "get_rpi_host_name",
    "get_device_id",
    "is_rpi",
]
