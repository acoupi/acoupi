"""Implementation of AudioRecorder for acoupi.

Audio recorder is used to record audio files. Audio recorder
(PyAudioRecorder) is implemented as class that inherit from
AudioRecorder. The class should implement the record() method which
return a temporary audio file based on the dataclass Recording. The
dataclass Recording takes a datetime.datetime object, a path from type
str, a duration from type float, and samplerate from type float.

The audio recorder takes arguments related to the audio device. It
specifies the acoutics parameters of recording an audio file. These are
the samplerate, the duration, the number of audio_channels, the chunk
size, and the index of the audio device. The index of the audio device
corresponds to the index of the USB port the device is connected to. The
audio recorder return a temporary .wav file.
"""

import datetime
import wave
from pathlib import Path
from typing import List, Optional

import click
import pyaudio
from celery.utils.log import get_task_logger
from pydantic import BaseModel

from acoupi import data
from acoupi.components.types import AudioRecorder
from acoupi.devices.audio import get_input_devices
from acoupi.system.exceptions import HealthCheckError, ParameterError

TMP_PATH = Path("/run/shm/")

__all__ = [
    "PyAudioRecorder",
    "MicrophoneConfig",
]


class PyAudioRecorder(AudioRecorder):
    """An AudioRecorder that records a 3 second audio file."""

    duration: float
    """The duration of the audio file in seconds."""

    samplerate: int
    """The samplerate of the audio file in Hz."""

    audio_channels: int
    """The number of audio channels."""

    device_name: str
    """The name of the input audio device."""

    chunksize: int
    """The chunksize of the audio file in bytes."""

    audio_dir: Path
    """The path of the audio file in temporary memory."""

    def __init__(
        self,
        duration: float,
        samplerate: int,
        audio_channels: int,
        device_name: str,
        chunksize: int = 8 * 2048,
        audio_dir: Path = TMP_PATH,
        logger=None,
    ) -> None:
        """Initialise the AudioRecorder with the audio parameters."""
        # Audio Duration
        self.duration = duration

        # Audio Microphone Parameters
        self.samplerate = samplerate
        self.audio_channels = audio_channels
        self.device_name = device_name

        # Audio Files Parameters
        self.chunksize = chunksize
        self.audio_dir = audio_dir
        self.sample_width = pyaudio.get_sample_size(pyaudio.paInt16)

        if logger is None:
            logger = get_task_logger(__name__)
        self.logger = logger

    def record(self, deployment: data.Deployment) -> data.Recording:
        """Record an audio file.

        Return the temporary path of the file.
        """
        now = datetime.datetime.now()
        temp_path = self.audio_dir / f'{now.strftime("%Y%m%d_%H%M%S")}.wav'
        frames = self.get_recording_data(duration=self.duration)
        self.save_recording(frames, temp_path)
        return data.Recording(
            path=temp_path,
            datetime=now,
            duration=self.duration,
            samplerate=self.samplerate,
            audio_channels=self.audio_channels,
            chunksize=self.chunksize,
            deployment=deployment,
        )

    def get_recording_data(
        self,
        duration: Optional[float] = None,
        num_chunks: Optional[int] = None,
    ) -> bytes:
        if num_chunks is None:
            if duration is None:
                raise ValueError("duration or num_chunks must be provided")

            num_chunks = int(duration * self.samplerate / self.chunksize)

        p = pyaudio.PyAudio()

        device = self.get_input_device(p)

        stream = p.open(
            format=pyaudio.paInt16,
            channels=self.audio_channels,
            rate=self.samplerate,
            input=True,
            frames_per_buffer=self.chunksize,
            input_device_index=device.index,
        )

        frames = []
        for _ in range(0, num_chunks if num_chunks > 0 else 1):
            audio_data = stream.read(
                self.chunksize,
                exception_on_overflow=True,
            )
            frames.append(audio_data)

        stream.stop_stream()
        stream.close()
        p.terminate()

        return b"".join(frames)

    def save_recording(self, data: bytes, path: Path) -> None:
        """Save the recording to a file."""

        with wave.open(str(path), "wb") as temp_audio_file:
            temp_audio_file.setnchannels(self.audio_channels)
            temp_audio_file.setsampwidth(self.sample_width)
            temp_audio_file.setframerate(self.samplerate)
            temp_audio_file.writeframes(data)

    def get_input_device(self, p: pyaudio.PyAudio):
        """Get the input device."""
        input_devices = get_input_devices(p)
        device = next(
            (d for d in input_devices if d.name == self.device_name), None
        )

        if device is None:
            raise ParameterError(
                value="device_name",
                message="The selected input device was not found.",
                help="Check if the microphone is connected.",
            )

        return device

    def check(self):
        """Check if the audio recorder is compatible with the config."""

        try:
            data = self.get_recording_data(num_chunks=1)
        except ParameterError as error:
            raise HealthCheckError(
                message=(
                    "The audio recorder is not compatible with the "
                    "selected microphone. Check the configurations."
                    f"Error: {error}"
                )
            ) from error
        except OSError as error:
            if "Invalid sample rate" in str(error):
                raise HealthCheckError(
                    message=(
                        "The audio recorder is not compatible with the "
                        "selected samplerate. Check the configurations."
                    )
                ) from error

            if "Invalid number of channels" in str(error):
                raise HealthCheckError(
                    message=(
                        "The audio recorder is not compatible with the "
                        "selected number of channels. Check the configurations."
                    )
                ) from error

            raise error

        if len(data) != self.chunksize * self.audio_channels * 2:
            raise HealthCheckError(
                message=(
                    "The audio recorder is not working properly. "
                    "Check the configurations."
                )
            )


class MicrophoneConfig(BaseModel):
    device_name: str
    samplerate: int = 48_000
    audio_channels: int = 1

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

    return MicrophoneConfig(
        device_name=selected_device.name,
        samplerate=samplerate,
        audio_channels=channels,
    )
