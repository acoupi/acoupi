from acoupi.devices.audio.pipewire import DeviceInfo, get_input_devices


class TestGetInputDevices:
    def test_returns_device_info(self):
        devices = get_input_devices()
        for device in devices:
            assert isinstance(device, DeviceInfo)
