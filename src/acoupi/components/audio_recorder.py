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
from typing import Tuple

import pyaudio
import sounddevice  # noqa: F401
from pydantic import BaseModel

from acoupi import data
from acoupi.components.types import AudioRecorder

TMP_PATH = Path("/run/shm/")

__all__ = [
    "PyAudioRecorder",
    "MicrophoneConfig",
]


class MicrophoneConfig(BaseModel):
    device_index: int = 0
    samplerate: int = 48_000
    audio_channels: int = 1

    def setup(self):
        """Setup the microphone configuration."""
        return


def has_input_audio_device() -> bool:
    """Check if there are any input audio devices available."""
    # Create an instance of PyAudio
    p = pyaudio.PyAudio()

    try:
        p.get_default_input_device_info()
        return True
    except IOError:
        return False


def get_microphone_info() -> Tuple[int, int, int]:
    """Check if there are any input audio devices available.
    And get the information of a compatible audio device.

    Parameters
    ----------
    samplerate : int
        The device default samplerate.
    audio_channels : int
        The default number of channels. The microphone should have at least
        one audio channel.
    device_index : int
        The input index of the audio device. The input index is linked to
        USB port the device is connected to.

    Returns
    -------
    samplerate : int
        The device default samplerate.

    Raises
    ------
    IOError
        If no compatible audio device is found.
    """

    # Create an instance of PyAudio
    p = pyaudio.PyAudio()
    try:
        p.get_default_input_device_info()

        # Get default input device info
        default_input_device = p.get_default_input_device_info()

        # Get the number of channels
        channels = int(default_input_device["maxInputChannels"])

        # Get the input device index
        input_device_index = int(default_input_device["index"])

        # Get the sample rate
        sample_rate = int(default_input_device["defaultSampleRate"])

        p.terminate()
        return channels, sample_rate, input_device_index

    except IOError:
        raise IOError("No compatible audio device found.")


class PyAudioRecorder(AudioRecorder):
    """An AudioRecorder that records a 3 second audio file."""

    duration: float
    """The duration of the audio file in seconds."""

    samplerate: int
    """The samplerate of the audio file in Hz."""

    audio_channels: int
    """The number of audio channels."""

    device_index: int
    """The input index of the audio device."""

    chunksize: int
    """The chunksize of the audio file in bytes."""

    audio_dir: Path
    """The path of the audio file in temporary memory."""

    def __init__(
        self,
        duration: float,
        samplerate: int,
        audio_channels: int,
        device_index: int,
        chunksize: int,
        audio_dir: Path = TMP_PATH,
    ) -> None:
        """Initialise the AudioRecorder with the audio parameters."""
        # Audio Duration
        self.duration = duration
        # Audio Microphone Parameters
        self.samplerate = samplerate
        self.audio_channels = audio_channels
        self.device_index = device_index
        # Audio Files Parameters
        self.chunksize = chunksize
        self.audio_dir = audio_dir

    def check(self):
        """Check if the audio recorder is compatible with the config."""
        return

    def record(self, deployment: data.Deployment) -> data.Recording:
        """Record a 3 second temporary audio file.

        Return the temporary path of the file.
        """
        self.datetime = datetime.datetime.now()

        # Specified the desired path for temporary file - Saved in RAM
        temp_path = (
            self.audio_dir / f'{self.datetime.strftime("%Y%m%d_%H%M%S")}.wav'
        )

        # Create a temporary file to record audio
        with open(temp_path, "wb") as temp_audiof:
            # Get the temporary file path from the created temporary audio file
            temp_audio_path = temp_audiof.name

            # Create an new instace of PyAudio
            p = pyaudio.PyAudio()

            (
                self.audio_channels,
                self.samplerate,
                self.device_index,
            ) = get_microphone_info()

            # Create new audio stream
            stream = p.open(
                format=pyaudio.paInt16,
                channels=self.audio_channels,
                rate=self.samplerate,
                input=True,
                frames_per_buffer=self.chunksize,
                input_device_index=self.device_index,
            )

            # Initialise array to store audio frames
            frames = []
            # Record audio - read the audio stream
            for _ in range(
                0, int(self.samplerate / self.chunksize * self.duration)
            ):
                audio_data = stream.read(
                    self.chunksize, exception_on_overflow=False
                )
                frames.append(audio_data)

            # Stop Recording and close the port interface
            stream.stop_stream()
            stream.close()
            p.terminate()

            # Create a WAV file to write the audio data
            with wave.open(temp_audio_path, "wb") as temp_audio_file:
                temp_audio_file.setnchannels(self.audio_channels)
                temp_audio_file.setsampwidth(
                    p.get_sample_size(pyaudio.paInt16)
                )
                temp_audio_file.setframerate(self.samplerate)

                # Write the audio data to the temporary file
                temp_audio_file.writeframes(b"".join(frames))
                temp_audio_file.close()

                # Create a Recording object and return it
                return data.Recording(
                    path=Path(temp_audio_path),
                    audio_channels=self.audio_channels,
                    datetime=self.datetime,
                    duration=self.duration,
                    samplerate=self.samplerate,
                    deployment=deployment,
                )
