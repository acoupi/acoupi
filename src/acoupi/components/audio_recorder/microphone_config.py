import argparse
from typing import List

import click
import pyaudio
from pydantic import BaseModel, Field

from acoupi.devices.audio.pyaudio import get_input_devices
from acoupi.system.config.parsers import parse_field_from_args
from acoupi.system.exceptions import ParameterError


class MicrophoneConfig(BaseModel):
    device_name: str
    samplerate: int = 48_000
    audio_channels: int = 1
    time_expansion: float = Field(default=1, gt=0)

    @classmethod
    def setup(
        cls,
        args: List[str],
        prompt: bool = True,
        prefix: str = "",
    ) -> "MicrophoneConfig":
        """Set up the microphone configuration."""
        return parse_microphone_config(args, prompt, prefix)


def parse_microphone_config(
    args: List[str],
    prompt: bool = True,
    prefix: str = "",
) -> MicrophoneConfig:
    # TODO: Adapt to use args, prompt and prefix
    click.secho("\n* Setting up microphone configuration.\n", fg="green")

    p = pyaudio.PyAudio()

    available_devices = get_input_devices(p)

    if len(available_devices) == 0:
        click.secho(
            "\n* No compatible audio device found.\n", fg="red", bold=True
        )
        raise ParameterError(
            value="device_index",
            message="No compatible audio device found.",
            help="Check if the microphone is connected.",
        )

    if not prompt:
        try:
            device_name = parse_field_from_args(
                "device_name",
                MicrophoneConfig.model_fields["device_name"],
                args,
                prompt=False,
                prefix=prefix,
            )

        except argparse.ArgumentError:
            device_name = available_devices[0].name

        try:
            device = next(
                d for d in available_devices if d.name == device_name
            )
        except StopIteration as error:
            raise ParameterError(
                value="device_name",
                message=f"No audio device with the name {device_name} found.",
                help="Check if the microphone is connected or review the "
                "available audio devices.",
            ) from error

        samplerate = parse_field_from_args(
            "samplerate",
            MicrophoneConfig.model_fields["samplerate"],
            args,
            prompt=False,
            prefix=prefix,
        )

        if not samplerate:
            samplerate = int(device.default_samplerate)

        channels = parse_field_from_args(
            "audio_channels",
            MicrophoneConfig.model_fields["audio_channels"],
            args,
            prompt=False,
            prefix=prefix,
        )

        time_expansion = parse_field_from_args(
            "time_expansion",
            MicrophoneConfig.model_fields["time_expansion"],
            args,
            prompt=False,
            prefix=prefix,
        )

        return MicrophoneConfig(
            device_name=device.name,
            samplerate=int(samplerate),  # type: ignore
            audio_channels=channels or 1,  # type: ignore
            time_expansion=time_expansion,  # type: ignore
        )

    click.secho("Available audio devices:\n", fg="green", bold=True)
    click.secho(
        f"{'Index':<7}{'Name':40}{'Channels':<10}{'Sample Rate':<10}",
        fg="green",
    )
    for device in available_devices:
        click.secho(f"[{device.index:>2}]   ", fg="green", bold=True, nl=False)
        click.echo(
            f"{device.name[:38]:<40}"
            f"{device.max_input_channels:<10}"
            f"{device.default_samplerate:<10}",
        )

    while True:
        try:
            index = click.prompt(
                "\nSelect an audio device index",
                type=click.Choice([str(d.index) for d in available_devices]),
                value_proc=int,
            )
            selected_device = next(
                d for d in available_devices if d.index == index
            )
            break
        except (ValueError, StopIteration):
            click.secho(
                "Invalid input. Please select a valid audio device index.",
                fg="red",
            )

    click.secho("\nInfo of selected audio device:\n", fg="green", bold=True)
    click.secho(
        f"{'index':20} = {selected_device.index}\n"
        f"{'name':20} = {selected_device.name}\n"
        f"{'max channels':20} = {selected_device.max_input_channels}\n"
        f"{'default sample rate':20} = {selected_device.default_samplerate}\n",
        fg="yellow",
    )

    while True:
        try:
            channels = click.prompt(
                "Select the number of audio channels",
                type=click.Choice(
                    [
                        str(i)
                        for i in range(
                            1, 1 + selected_device.max_input_channels
                        )
                    ]
                ),
                value_proc=int,
                default=selected_device.max_input_channels,
            )
            if channels > selected_device.max_input_channels:
                raise ValueError
            break
        except ValueError:
            click.secho(
                "Invalid input. Please select a valid "
                "number of audio channels.",
                fg="red",
            )

    while True:
        try:
            samplerate = click.prompt(
                "\nSelect the samplerate. The default samplerate is "
                "recommended but your device might support other "
                "sampling rates.",
                type=int,
                default=selected_device.default_samplerate,
            )
            if p.is_format_supported(
                samplerate,
                input_device=selected_device.index,
                input_channels=channels,
                input_format=pyaudio.paInt16,
            ):
                break
        except ValueError as error:
            if error.args[0] == "Invalid sample rate":
                click.secho(
                    "Samplerate not supported by the audio device.",
                    fg="red",
                )
                click.secho(
                    "Please try with another samplerate. "
                    "We recommend you consult the documentation of your "
                    "audio device to find the supported samplerates.",
                    fg="yellow",
                )
            else:
                click.secho(
                    "Invalid input. Please select a valid samplerate.",
                    fg="red",
                )

    time_expansion = click.prompt(
        "Adjust the playback speed/duration metadata for downstream analysis.\n"
        "Example: Enter 10.0 if you recorded at 480kHz but need to process at 48kHz.\n"
        "Enter the time expansion factor (default: 1.0). \n",
        type=click.FloatRange(min=0.0, clamp=False, min_open=True),
        default=1.0,
    )

    return MicrophoneConfig(
        device_name=selected_device.name,
        samplerate=samplerate,
        audio_channels=channels,
        time_expansion=time_expansion,
    )
