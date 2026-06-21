from argparse import ArgumentParser
from pathlib import Path
from subprocess import TimeoutExpired, run

import click
from pydantic import BaseModel, Field

from acoupi.components.audio_recorder.base import TMP_PATH, BaseAudioRecorder
from acoupi.devices.audio.pipewire import (
    DeviceInfo,
    get_input_device_by_name,
    get_input_devices,
)
from acoupi.system.exceptions import (
    DeviceUnavailableError,
    ParameterError,
    RecordingError,
)


class PWRecorder(BaseAudioRecorder):
    def __init__(
        self,
        duration: float,
        samplerate: int,
        audio_channels: int,
        device_name: str,
        audio_dir: Path = TMP_PATH,
        time_expansion: float = 1,
    ):
        super().__init__(
            duration=duration,
            samplerate=samplerate,
            audio_channels=audio_channels,
            device_name=device_name,
            audio_dir=audio_dir,
            time_expansion=time_expansion,
        )

    def generate_recording(
        self,
        path: Path,
        duration: float | None = None,
    ) -> None:
        """Generate an audio recording."""
        return record_audio(
            path=path,
            samplerate=self.samplerate,
            audio_channels=self.audio_channels,
            device_name=self.device_name,
            duration=duration or self.duration,
        )


def record_audio(
    path: Path,
    samplerate: int,
    audio_channels: int,
    device_name: str,
    duration: float,
) -> None:
    samples = int(duration * samplerate)
    cmd = [
        "pw-record",
        f"--rate={samplerate}",
        f"--channels={audio_channels}",
        f"--sample-count={samples}",
        f"--target={device_name}",
        str(path),
    ]

    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=duration + 2,
        )
    except FileNotFoundError as error:
        raise DeviceUnavailableError(
            message="The pw-record command was not found.",
            help="Install PipeWire tools and check that pw-record is on PATH.",
        ) from error
    except TimeoutExpired as error:
        raise RecordingError(
            message="The pw-record command did not finish within the expected time.",
            help="Check that PipeWire is running and the selected device is responsive.",
        ) from error

    if not path.exists():
        raise RecordingError(
            message="PipeWire failed to record audio",
            help="Check that the selected microphone exists and supports the requested settings.",
        )


class PWMicrophoneConfig(BaseModel):
    device_name: str
    samplerate: int = 48_000
    audio_channels: int = 1
    time_expansion: float = Field(default=1, gt=0)

    @classmethod
    def setup(
        cls,
        args: list[str],
        prompt: bool = True,
        prefix: str = "",
    ) -> "PWMicrophoneConfig":
        """Set up the microphone configuration."""
        return _parse_pw_microphone_config(args, prompt, prefix)


def _parse_pw_microphone_config(
    args: list[str],
    prompt: bool = True,
    prefix: str = "",
) -> PWMicrophoneConfig:
    """Parse the microphone configuration."""
    parser = ArgumentParser(description="Microphone configuration")
    parser.add_argument(
        f"--{prefix}device-name",
        dest="device_name",
        type=str,
        help="The name of the microphone device",
        default=None,
    )
    parser.add_argument(
        f"--{prefix}samplerate",
        dest="samplerate",
        type=int,
        help="The samplerate of the microphone",
        default=None,
    )
    parser.add_argument(
        f"--{prefix}audio-channels",
        dest="audio_channels",
        type=int,
        help="The number of audio channels",
        default=None,
    )

    parsed, _ = parser.parse_known_args(args)

    available_devices = get_input_devices()

    if parsed.device_name is None:
        if not prompt:
            raise ParameterError(
                value="device_name",
                message="No microphone device name provided.",
                help="Provide --device-name or enable prompting.",
            )

        parsed.device_name = _prompt_device_choice(available_devices)

    try:
        selected_device = get_input_device_by_name(parsed.device_name)
    except DeviceUnavailableError as error:
        raise ParameterError(
            value="device_name",
            message=f"No device found with name {parsed.device_name}.",
            help="Check the available PipeWire input devices and try again.",
        ) from error

    if parsed.samplerate is None:
        if not prompt:
            raise ParameterError(
                value="samplerate",
                message="No samplerate provided.",
                help="Provide --samplerate or enable prompting.",
            )

        rates = [str(rate) for rate in sorted(selected_device.samplerates)]

        if not rates:
            raise ParameterError(
                value="samplerate",
                message="No samplerates available.",
                help="Check that the selected PipeWire device exposes supported formats.",
            )

        default = None
        if len(rates) == 1:
            default = rates[0]

        choice = click.prompt(
            "What samplerate do you want to use?",
            type=click.Choice(rates),
            default=default,
        )
        parsed.samplerate = choice

    if parsed.audio_channels is None:
        if not prompt:
            raise ParameterError(
                value="audio_channels",
                message="No audio channels provided.",
                help="Provide --audio-channels or enable prompting.",
            )

        choice = click.prompt(
            "How many audio channels do you want to use?",
            type=click.Choice([1, 2]),
            default=1,
        )
        parsed.audio_channels = choice

    return PWMicrophoneConfig(
        device_name=parsed.device_name,
        samplerate=int(parsed.samplerate),
        audio_channels=int(parsed.audio_channels),
    )


def _prompt_device_choice(devices: list[DeviceInfo]) -> str:
    if not devices:
        raise ParameterError(
            value="device_name",
            message="No compatible PipeWire input devices found.",
            help="Check that the microphone is connected and PipeWire is running.",
        )

    click.secho(
        "Available microphones:\n",
        fg="green",
        bold=True,
    )
    for i, device in enumerate(devices):
        click.secho(f"[{i:>2}]   ", fg="green", bold=True, nl=False)
        click.echo(_format_device_choice(device))

    default = None
    if len(devices) == 1:
        default = "0"

    choice = click.prompt(
        "Which microphone do you want to use?",
        type=click.Choice([str(i) for i in range(len(devices))]),
        default=default,
    )

    return devices[int(choice)].name


def _format_device_choice(device: DeviceInfo) -> str:
    return (
        f"{device.description} "
        f"[{device.max_input_channels} ch, rates={sorted(device.samplerates)}]"
    )
