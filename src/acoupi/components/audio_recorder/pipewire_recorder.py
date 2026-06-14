import datetime
import json
from argparse import ArgumentParser
from pathlib import Path
from subprocess import run

import click
from pydantic import BaseModel, Field

from acoupi import data
from acoupi.components.types import AudioRecorder

TMP_PATH = Path("/run/shm/")


class PWRecorder(AudioRecorder):
    duration: float

    samplerate: int

    audio_channels: int

    device_name: str

    audio_dir: Path

    def __init__(
        self,
        duration: float,
        samplerate: int,
        audio_channels: int,
        device_name: str,
        audio_dir: Path = TMP_PATH,
    ):
        self.duration = duration

        self.samplerate = samplerate
        self.audio_channels = audio_channels
        self.device_name = device_name

        self.audio_dir = audio_dir

    def record(self, deployment: data.Deployment) -> data.Recording:
        """Record an audio file."""
        now = data.utc_now()
        temp_path = self.audio_dir / f"{now.strftime('%Y%m%d_%H%M%S')}.wav"

        pw_record_audio(
            path=temp_path,
            duration=self.duration,
            samplerate=self.samplerate,
            audio_channels=self.audio_channels,
            device_name=self.device_name,
        )

        return data.Recording(
            path=temp_path,
            created_on=now,
            duration=self.duration,
            samplerate=self.samplerate,
            audio_channels=self.audio_channels,
            deployment=deployment,
        )


def pw_record_audio(
    path: Path,
    duration: float,
    samplerate: int,
    audio_channels: int,
    device_name: str,
) -> None:
    cmd = [
        "pw-record",
        "--format=s16",
        f"--rate={samplerate}",
        f"--channels={audio_channels}",
        f"--duration={duration}",
        f"--target={device_name}",
        str(path),
    ]

    run(cmd, capture_output=True, check=True)


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
            raise ValueError("No microphone device name provided")

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
        raise ValueError(f"No device found with name {parsed.device_name}")

    if parsed.samplerate is None:
        if not prompt:
            raise ValueError("No samplerate provided")

        rates = [
            str(fmt.get("rate"))
            for fmt in selected_device["params"]["EnumFormat"]
            if fmt.get("rate")
        ]

        if not rates:
            raise ValueError("No samplerates available")

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
            raise ValueError("No audio channels provided")

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
    devices = json.loads(
        run(["pw-dump"], capture_output=True, text=True).stdout
    )
    return [
        device["info"]
        for device in devices
        if device["type"] == "PipeWire:Interface:Node"
        and device.get("info").get("props").get("media.class")
        == "Audio/Source"
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
        default = info[0]["value"]

    choice = click.prompt(
        "Which microphone do you want to use?",
        type=click.Choice(range(len(info))),
        default=default,
    )

    return info[choice]["value"]


def _get_device_choice(pw_info) -> dict:
    rates = [fmt.get("rate") for fmt in pw_info["params"]["EnumFormat"]]
    return dict(
        title=f"{pw_info['props']['node.description']} {rates}",
        value=pw_info["props"]["node.name"],
    )
