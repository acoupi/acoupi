"""PyAudio-backed audio recorder and recorder configuration."""

import argparse
import math
import wave
from pathlib import Path
from typing import List

import click
import pyaudio
from pydantic import BaseModel, Field

from acoupi.components.audio_recorder.base import BaseAudioRecorder
from acoupi.devices.audio.pyaudio import (
    get_input_device_by_name,
    get_input_devices,
)
from acoupi.system.config.parsers import parse_field_from_args
from acoupi.system.exceptions import (
    DeviceConfigurationError,
    ParameterError,
    RecordingError,
)

TMP_PATH = Path("/run/shm/")

__all__ = [
    "PARecorder",
    "PARecorderConfig",
    "MicrophoneConfig",
    "PyAudioRecorder",
    "record_audio",
]


class PARecorder(BaseAudioRecorder):
    """Audio recorder implementation backed by PyAudio.

    This recorder captures PCM audio from a named PyAudio input device and
    stores the result as a WAV file.

    Use [`check`][.check] before deployment to verify that the selected device,
    samplerate, number of channels, and chunk size work reliably on the target
    machine.
    """

    duration: float
    """The duration of the audio file in seconds."""

    samplerate: int
    """The samplerate of the audio file in Hz."""

    audio_channels: int
    """The number of audio channels."""

    device_name: str
    """The name of the input audio device."""

    chunksize: int
    """Number of audio frames read from the device per stream read.

    This value controls how much audio is pulled from the device each time the
    recorder reads from the PyAudio stream. Lower values reduce buffering but
    increase the number of read calls. Higher values reduce Python overhead but
    can increase latency and may interact differently with device drivers.

    Some devices are sensitive to this setting. If recording fails, drops
    samples, or behaves unreliably despite a valid device and samplerate, try
    adjusting ``chunksize``. In practice, trying a different power-of-two value
    is often the most effective fix.
    """

    audio_dir: Path
    """The directory where to store the created recordings."""

    time_expansion: float
    """Factor used to reinterpret the recording timescale downstream.

    This does not change the way audio is captured from the device. Instead, it
    adjusts the stored samplerate metadata after recording so downstream tools
    analyse the file at a slower or faster effective timescale.
    """

    def __init__(
        self,
        duration: float,
        samplerate: int,
        audio_channels: int,
        device_name: str,
        chunksize: int = 2048,
        audio_dir: Path = TMP_PATH,
        time_expansion: float = 1,
    ) -> None:
        """Initialise a PyAudio recorder.

        Parameters
        ----------
        duration:
            Default recording duration in seconds.
        samplerate:
            Recording samplerate in Hz.
        audio_channels:
            Number of input channels to capture.
        device_name:
            Name of the PyAudio input device.
        chunksize:
            Number of audio frames read from the device per stream read.
            If recording fails unexpectedly on a working device, this is one of
            the first values worth adjusting.
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

        self.sample_width = pyaudio.get_sample_size(pyaudio.paInt16)
        self.chunksize = chunksize

    def generate_recording(
        self,
        path: Path,
        duration: float | None = None,
    ) -> None:
        """Record audio to ``path`` using PyAudio.

        Raises
        ------
        DeviceConfigurationError
            If the requested samplerate or channel count is unsupported.
        RecordingError
            If recording starts but fails unexpectedly.
        """
        frames = record_audio(
            samplerate=self.samplerate,
            audio_channels=self.audio_channels,
            device_name=self.device_name,
            duration=duration or self.duration,
            chunksize=self.chunksize,
        )
        save_wav_to_file(
            frames,
            path,
            audio_channels=self.audio_channels,
            sample_width=self.sample_width,
            samplerate=self.samplerate,
        )


def record_audio(
    samplerate: int,
    audio_channels: int,
    device_name: str,
    duration: float | None = None,
    num_chunks: int | None = None,
    chunksize: int = 2048,
) -> bytes:
    """Record audio samples from a PyAudio input device.

    Raises
    ------
    ValueError
        If neither ``duration`` nor ``num_chunks`` is provided.
    DeviceConfigurationError
        If the requested samplerate or channel count is unsupported.
    RecordingError
        If PyAudio fails while opening or reading from the stream.
    """
    if num_chunks is None:
        if duration is None:
            raise ValueError("duration or num_chunks must be provided")

        # NOTE: Round up to the nearest chunk otherwise the recording will
        # be shorter than the requested duration
        num_chunks = math.ceil(duration * samplerate / chunksize)

    if duration is None:
        duration = num_chunks * chunksize / samplerate

    p = pyaudio.PyAudio()

    device = get_input_device_by_name(p, device_name)

    try:
        stream = p.open(
            format=pyaudio.paInt16,
            channels=audio_channels,
            rate=samplerate,
            input=True,
            frames_per_buffer=2048,
            input_device_index=device.index,
        )
    except OSError as error:
        message = str(error)
        if "Invalid sample rate" in message:
            raise DeviceConfigurationError(
                message=(
                    "The audio recorder is not compatible with the selected "
                    "samplerate. Check the configurations."
                )
            ) from error

        if "Invalid number of channels" in message:
            raise DeviceConfigurationError(
                message=(
                    "The audio recorder is not compatible with the selected "
                    "number of channels. Check the configurations."
                )
            ) from error

        raise RecordingError(message=message) from error

    frames = []
    for _ in range(0, num_chunks if num_chunks > 0 else 1):
        audio_data = stream.read(chunksize, exception_on_overflow=True)
        frames.append(audio_data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    wavdata = b"".join(frames)

    # NOTE: Due to the rounding up of the number of chunks, the recording
    # might be longer than the requested duration. We need to truncate the
    # data to the expected length.
    expected_length = int(2 * samplerate * duration * audio_channels)
    if len(wavdata) > expected_length:
        wavdata = wavdata[:expected_length]

    return wavdata


def save_wav_to_file(
    wavdata: bytes,
    path: Path,
    audio_channels: int = 1,
    sample_width: int = 2,
    samplerate: int = 48000,
) -> None:
    """Write raw PCM frame bytes to a WAV file."""
    with wave.open(str(path), "wb") as temp_audio_file:
        temp_audio_file.setnchannels(audio_channels)
        temp_audio_file.setsampwidth(sample_width)
        temp_audio_file.setframerate(samplerate)
        temp_audio_file.writeframes(wavdata)


class PARecorderConfig(BaseModel):
    """Configuration values required to build a ``PARecorder``."""

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
    ) -> "PARecorderConfig":
        """Create recorder configuration from CLI-style arguments."""
        return parse_microphone_config(args, prompt, prefix)


def parse_microphone_config(
    args: List[str],
    prompt: bool = True,
    prefix: str = "",
) -> PARecorderConfig:
    """Parse PyAudio recorder configuration from command-line arguments."""
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
                PARecorderConfig.model_fields["device_name"],
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
            PARecorderConfig.model_fields["samplerate"],
            args,
            prompt=False,
            prefix=prefix,
        )

        if not samplerate:
            samplerate = int(device.default_samplerate)

        channels = parse_field_from_args(
            "audio_channels",
            PARecorderConfig.model_fields["audio_channels"],
            args,
            prompt=False,
            prefix=prefix,
        )

        time_expansion = parse_field_from_args(
            "time_expansion",
            PARecorderConfig.model_fields["time_expansion"],
            args,
            prompt=False,
            prefix=prefix,
        )

        return PARecorderConfig(
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

    return PARecorderConfig(
        device_name=selected_device.name,
        samplerate=samplerate,
        audio_channels=channels,
        time_expansion=time_expansion,
    )


# Backwards-compatible aliases for the public component API.
PyAudioRecorder = PARecorder
MicrophoneConfig = PARecorderConfig
