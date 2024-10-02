"""Test the utils module."""

import unittest.mock as um

import pytest

from acoupi import devices

TEST_CPUINFO = """
Serial          =  00000000a3123456
MAC-address(es) =  b8:27:eb:12:34:56 b8:27:eb:ab:cd:ef
Revision        =  a020d3
PCBRevision     =  3
ModelName       =  3B+
Processor       =  BCM2837
Manufacturer    =  Sony UK
MemorySize      =  1024 MB
EncodedFlag     =  revision is a bit field
WarrantyVoidOld =  no
WarrantyVoidNew =  no
"""


def test_get_device_serial() -> None:
    """Test the get_device_serial function."""
    # Need to mock the open function to test if not in a device
    with um.patch("builtins.open", um.mock_open(read_data=TEST_CPUINFO)):
        serial = devices.get_device_serial_number()
        assert len(serial) == 16


def test_patched_device_serial_number(
    patched_device_serial_number: str,
) -> None:
    """Test the patched_device_serial_number fixture."""
    serial = devices.get_device_serial_number()
    assert patched_device_serial_number == "1234567890ABCDEF"
    assert patched_device_serial_number == serial


@pytest.mark.skipif(
    not devices.is_rpi(),
    reason="Test only runs on Raspberry Pi",
)
def test_get_device_hostname():
    """Test the get_device_host_name function."""
    assert devices.get_device_host_name() == "pi"
