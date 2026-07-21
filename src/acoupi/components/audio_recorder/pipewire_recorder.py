"""PipeWire-backed audio recorder and recorder configuration."""

from argparse import ArgumentParser
from pathlib import Path
from subprocess import TimeoutExpired, run

import click
from pydantic import BaseModel, Field

from acoupi.components.audio_recorder.base import TMP_PATH, BaseAudioRecorder
from acoupi.devices.audio.pipewire import DeviceInfo, get_input_devices
from acoupi.system.exceptions import (
    DeviceUnavailableError,
    ParameterError,
    RecordingError,
)


class PWRecorder(BaseAudioRecorder):
    """Audio recorder implementation that shells out to ``pw-record``.

    This recorder delegates capture to PipeWire command-line tools instead of
    reading audio frames directly through Python.

    Use [`check`][.check] before deployment to verify that the selected device and
    recording parameters work on the target machine.
    """

    def __init__(
        self,
        duration: float,
        samplerate: int,
        audio_channels: int,
        device_name: str,
        audio_dir: Path = TMP_PATH,
        time_expansion: float = 1,
    ):
        """Initialise a PipeWire recorder.

        Parameters
        ----------
        duration:
            Default recording duration in seconds.
        samplerate:
            Recording samplerate in Hz.
        audio_channels:
            Number of input channels to capture.
        device_name:
            PipeWire target device name.
        audio_dir:
            Directory where recorded WAV files will be written.
        time_expansion:
            Metadata factor used to reinterpret the recording timescale
            downstream.

        Raises
        ------
        ValueError
            If ``time_expansion`` is not greater than zero.
        """
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
        """Record audio to ``path`` using PipeWire tools.

        Raises
        ------
        DeviceUnavailableError
            If the PipeWire recording command is unavailable.
        RecordingError
            If recording fails or no output file is produced.
        """
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
    """Record audio with ``pw-record``.

    Parameters
    ----------
    path:
        Destination path for the recorded WAV file.
    samplerate:
        Requested recording samplerate in Hz.
    audio_channels:
        Requested number of input channels.
    device_name:
        PipeWire target device name.
    duration:
        Recording duration in seconds.

    Raises
    ------
    DeviceUnavailableError
        If ``pw-record`` is not available on the system.
    RecordingError
        If the command times out or does not produce an output file.
    """
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


class PWRecorderConfig(BaseModel):
    """Configuration values required to build a ``PWRecorder``."""

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
    ) -> "PWRecorderConfig":
        """Create recorder configuration from CLI-style arguments."""
        return _parse_pw_microphone_config(args, prompt, prefix)


def _parse_pw_microphone_config(
    args: list[str],
    prompt: bool = True,
    prefix: str = "",
) -> PWRecorderConfig:
    """Parse PipeWire recorder configuration from command-line arguments.

    When prompting, channel choices are constrained by the selected device's
    advertised maximum input channels. Samplerate is treated as the requested
    PipeWire recording rate.
    """
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
        help="The requested recording samplerate",
        default=None,
    )
    parser.add_argument(
        f"--{prefix}audio-channels",
        dest="audio_channels",
        type=int,
        help="The requested number of input audio channels",
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
        selected_device = next(
            (
                device
                for device in available_devices
                if device.name == parsed.device_name
            )
        )
    except StopIteration as error:
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
            type=click.IntRange(min=8_000, max=384_000),
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
            type=click.IntRange(
                min=1,
                max=max(1, selected_device.max_input_channels),
            ),
            default=1,
        )
        parsed.audio_channels = choice

    return PWRecorderConfig(
        device_name=parsed.device_name,
        samplerate=int(parsed.samplerate),
        audio_channels=int(parsed.audio_channels),
    )


def _prompt_device_choice(devices: list[DeviceInfo]) -> str:
    """Prompt the user to choose a PipeWire input device."""
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
    """Format a concise device label for interactive prompts."""
    return (
        f"{device.description} "
        f"[{device.max_input_channels} ch, rates={sorted(device.samplerates)}]"
    )
