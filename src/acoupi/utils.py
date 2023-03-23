"""General utility functions for the project."""


__all__ = [
    "get_rpi_serial_number",
]


def get_rpi_serial_number() -> str:
    """Get the serial number of the Raspberry Pi.
 
    Returns:
        The serial number of the Raspberry Pi as a string.
    """
    with open("/proc/cpuinfo", "r") as f:
        for line in f:
            if line[0:6] == "Serial":
                return line[10:26]
    raise RuntimeError("Could not find serial number of Raspberry Pi")
