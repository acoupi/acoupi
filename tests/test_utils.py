"""Test the utils module."""
import unittest.mock as um
from acoupi import utils


TEST_CPUINFO = '''
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
'''


def test_get_rpi_serial() -> None:
    """Test the get_rpi_serial function."""
    # Need to mock the open function to test if not in a RPi
    with um.patch('builtins.open', um.mock_open(read_data=TEST_CPUINFO)):
        serial = utils.get_rpi_serial_number()
        assert len(serial) == 16


def test_patched_rpi_serial_number(patched_rpi_serial_number: str) -> None:
    """Test the patched_rpi_serial_number fixture."""
    serial = utils.get_rpi_serial_number()
    assert patched_rpi_serial_number == '1234567890ABCDEF'
    assert patched_rpi_serial_number == serial
