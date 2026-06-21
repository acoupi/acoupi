import json
from argparse import ArgumentParser
from pathlib import Path
from subprocess import CalledProcessError, TimeoutExpired, run

import click
from pydantic import BaseModel, Field

from acoupi.components.audio_recorder.base import TMP_PATH, BaseAudioRecorder
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

    device_info = _get_pw_device_info()

    if parsed.device_name is None:
        if not prompt:
            raise ParameterError(
                value="device_name",
                message="No microphone device name provided.",
                help="Provide --device-name or enable prompting.",
            )

        parsed.device_name = _prompt_device_choice(device_info)

    selected_device = next(
        (
            info
            for info in device_info
            if info["props"]["node.name"] == parsed.device_name
        ),
        None,
    )

    if selected_device is None:
        raise ParameterError(
            value="device_name",
            message=f"No device found with name {parsed.device_name}.",
            help="Check the available PipeWire input devices and try again.",
        )

    if parsed.samplerate is None:
        if not prompt:
            raise ParameterError(
                value="samplerate",
                message="No samplerate provided.",
                help="Provide --samplerate or enable prompting.",
            )

        rates = [
            str(fmt.get("rate"))
            for fmt in selected_device["params"]["EnumFormat"]
            if fmt.get("rate")
        ]

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
        samplerate=parsed.samplerate,
        audio_channels=parsed.audio_channels,
    )


def _get_pw_device_info():
    try:
        result = run(["pw-dump"], capture_output=True, text=True, check=True)
    except FileNotFoundError as error:
        raise DeviceUnavailableError(
            message="The pw-dump command was not found.",
            help="Install PipeWire tools and check that pw-dump is on PATH.",
        ) from error
    except CalledProcessError as error:
        stderr = (error.stderr or "").strip()
        raise DeviceUnavailableError(
            message="Failed to query PipeWire devices"
            + (f": {stderr}" if stderr else "."),
            help="Check that PipeWire is running and accessible.",
        ) from error

    devices = json.loads(result.stdout)
    return [
        info
        for device in devices
        if device.get("type") == "PipeWire:Interface:Node"
        and (info := device.get("info")) is not None
        and info.get("props", {}).get("media.class") == "Audio/Source"
    ]


def _prompt_device_choice(device_info) -> str:
    info = [_get_device_choice(info) for info in device_info]

    click.secho(
        "Available microphones:\n",
        fg="green",
        bold=True,
    )
    for i, device in enumerate(info):
        click.secho(f"[{i:>2}]   ", fg="green", bold=True, nl=False)
        click.echo(device["title"])

    default = None
    if len(info) == 1:
        default = "0"

    choice = click.prompt(
        "Which microphone do you want to use?",
        type=click.Choice([str(i) for i in range(len(info))]),
        default=default,
    )

    return info[int(choice)]["value"]


def _get_device_choice(pw_info) -> dict:
    rates = [
        fmt.get("rate")
        for fmt in pw_info.get("params", {}).get("EnumFormat", [])
        if fmt.get("rate") is not None
    ]

    return dict(
        title=(
            f"{pw_info.get('props', {}).get('node.description', 'Unknown device')}"
            f" {rates}"
        ),
        value=pw_info.get("props", {}).get("node.name"),
    )
