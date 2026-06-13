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
from typing import Optional

import pyaudio
from celery.utils.log import get_task_logger

from acoupi import data
from acoupi.components.types import AudioRecorder
from acoupi.devices.audio import get_input_device_by_name
from acoupi.system.exceptions import HealthCheckError, ParameterError

TMP_PATH = Path("/run/shm/")

__all__ = [
    "PyAudioRecorder",
]


class PyAudioRecorder(AudioRecorder):
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
        logger=None,
        time_expansion: float = 1,
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
        self.time_expansion = time_expansion

        if self.time_expansion <= 0:
            raise ValueError("time_expansion must be greater than 0")

        if logger is None:
            logger = get_task_logger(__name__)
        self.logger = logger

    def record(self, deployment: data.Deployment) -> data.Recording:
        """Record an audio file.

        Returns
        -------
        data.Recording: A Recording object containing the temporary path of the file.
        """
        now = data.utc_now()
        temp_path = self.audio_dir / f"{now.strftime('%Y%m%d_%H%M%S')}.wav"
        frames = self.get_recording_data(duration=self.duration)
        self.save_recording(frames, temp_path)

        return data.Recording(
            path=temp_path,
            created_on=now,
            duration=self.duration,
            samplerate=self.samplerate,
            audio_channels=self.audio_channels,
            time_expansion=self.time_expansion,
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

            # NOTE: Round up to the nearest chunk otherwise the recording will
            # be shorter than the requested duration
            num_chunks = math.ceil(duration * self.samplerate / self.chunksize)

        if duration is None:
            duration = num_chunks * self.chunksize / self.samplerate

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

        data = b"".join(frames)

        # NOTE: Due to the rounding up of the number of chunks, the recording
        # might be longer than the requested duration. We need to truncate the
        # data to the expected length.
        expected_length = int(
            2 * self.samplerate * duration * self.audio_channels
        )
        if len(data) > expected_length:
            data = data[:expected_length]

        return data

    def get_expanded_samplerate(self):
        return int(self.samplerate / self.time_expansion)

    def save_recording(self, data: bytes, path: Path) -> None:
        """Save the recording to a file."""
        with wave.open(str(path), "wb") as temp_audio_file:
            temp_audio_file.setnchannels(self.audio_channels)
            temp_audio_file.setsampwidth(self.sample_width)
            temp_audio_file.setframerate(self.get_expanded_samplerate())
            temp_audio_file.writeframes(data)

    def get_input_device(self, p: pyaudio.PyAudio):
        """Get the input device."""
        try:
            device = get_input_device_by_name(p, self.device_name)
        except IOError as error:
            raise ParameterError(
                value="device_name",
                message=(
                    "The selected input device was not found. "
                    f"Device name: {self.device_name}"
                ),
                help="Check if the microphone is connected.",
            ) from error

        return device

    def check(self):
        """Check if the audio recorder is compatible with the config."""
        num_chunks = 20
        try:
            data = self.get_recording_data(num_chunks=num_chunks)
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

        if len(data) != self.chunksize * self.audio_channels * 2 * num_chunks:
            raise HealthCheckError(
                message=(
                    "The audio recorder is not working properly. "
                    "Check the configurations."
                )
            )
