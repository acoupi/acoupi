"""Implementation of AudioRecorder for acoupi.

An AudioRecorder is used to record audio files.
The PyAudioRecorder is implemented as class that inherit from
`AudioRecorder`. The class should implement the record() method which
return a temporary audio file based on the dataclass Recording.

The audio recorder takes argument related to the audio device. It
specifies the acoutics parameters of recording an audio file. These are
the samplerate, the duration, the number of audio_channels, the chunk
size, and the index of the audio device. The index of the audio device
corresponds to the index of the USB port the device is connected to. The
audio recorder return a temporary .wav file.
"""

import math
import wave
from pathlib import Path

import pyaudio

from acoupi.components.audio_recorder.base import BaseAudioRecorder
from acoupi.devices.audio.pyaudio import get_input_device_by_name
from acoupi.system.exceptions import (
    DeviceConfigurationError,
    DeviceUnavailableError,
    HealthCheckError,
    RecordingError,
)

TMP_PATH = Path("/run/shm/")

__all__ = [
    "PyAudioRecorder",
    "record_audio",
]


class PyAudioRecorder(BaseAudioRecorder):
    """Component that records fixed duration audio to a file."""

    duration: float
    """The duration of the audio file in seconds."""

    samplerate: int
    """The samplerate of the audio file in Hz."""

    audio_channels: int
    """The number of audio channels."""

    device_name: str
    """The name of the input audio device."""

    chunksize: int

    audio_dir: Path
    """The directory where to store the created recordings."""

    time_expansion: float
    """The time expansion factor for the recording."""

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
        """Initialise the AudioRecorder with the audio parameters."""
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
        """Generate an audio recording."""
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
    """Record audio from the microphone."""
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
    """Save the wav data to a file."""
    with wave.open(str(path), "wb") as temp_audio_file:
        temp_audio_file.setnchannels(audio_channels)
        temp_audio_file.setsampwidth(sample_width)
        temp_audio_file.setframerate(samplerate)
        temp_audio_file.writeframes(wavdata)
