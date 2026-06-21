import struct
import tempfile
import wave
from abc import abstractmethod
from dataclasses import dataclass
from math import isclose
from pathlib import Path
from typing import BinaryIO

from acoupi import data
from acoupi.components.types import AudioRecorder
from acoupi.system.exceptions import (
    DeviceConfigurationError,
    DeviceUnavailableError,
    HealthCheckError,
    RecordingError,
)

TMP_PATH = Path("/run/shm/")


@dataclass
class MediaInfo:
    """Information about the media."""

    duration: float
    """Duration of the media in seconds."""

    samplerate: int
    """Samplerate of the media."""

    audio_channels: int
    """Number of audio channels in the media."""

    frames: int
    """Number of frames in the media."""


class BaseAudioRecorder(AudioRecorder):
    """Base class for audio recorders."""

    duration: float
    """Duration of each audio recording in seconds."""

    samplerate: int
    """Samplerate of the audio recording."""

    audio_channels: int
    """Number of audio channels in the recording."""

    device_name: str
    """Name of the input audio device."""

    audio_dir: Path
    """Directory where to store the recordings."""

    time_expansion: float = 1
    """Factor by which the recording's time scale is multiplied.

    Values > 1.0 indicate time expansion (slowing down playback), while values
    between 0.0 and 1.0 indicate time compression (speeding up playback).
    """

    def __init__(
        self,
        duration: float,
        samplerate: int,
        audio_channels: int,
        device_name: str,
        audio_dir: Path = TMP_PATH,
        time_expansion: float = 1,
        **kwargs,
    ):
        self.duration = duration

        self.samplerate = samplerate
        self.audio_channels = audio_channels
        self.device_name = device_name

        self.audio_dir = Path(audio_dir)
        self.time_expansion = time_expansion

        if self.time_expansion <= 0:
            raise ValueError("time_expansion must be greater than 0")

        if not self.audio_dir.exists():
            self.audio_dir.mkdir(parents=True)

    def record(self, deployment: data.Deployment) -> data.Recording:
        """Record an audio file.

        Returns
        -------
        data.Recording: A Recording object containing the temporary path of the file.
        """
        now = data.utc_now()
        temp_path = self.audio_dir / f"{now.strftime('%Y%m%d_%H%M%S')}.wav"

        self.generate_recording(temp_path)

        self.adjust_time_expansion(temp_path)

        return data.Recording(
            path=temp_path,
            created_on=now,
            duration=self.duration,
            samplerate=self.samplerate,
            audio_channels=self.audio_channels,
            deployment=deployment,
            time_expansion=self.time_expansion,
        )

    def adjust_time_expansion(self, path: Path) -> None:
        """Adjust the time expansion of the recording.

        This method is called by the `record` method to adjust the time
        expansion of the recording. It should be implemented by subclasses.

        Parameters
        ----------
        path : Path
            The path of the recording.
        """
        expanded_samplerate = self.get_expanded_samplerate()

        if expanded_samplerate == self.samplerate:
            return

        patch_samplerate(path, expanded_samplerate)

    def get_expanded_samplerate(self):
        """Get the expanded samplerate of the recording.

        This method is called by the `adjust_time_expansion` method to get the
        expanded samplerate of the recording. It should be implemented by
        subclasses.

        Returns
        -------
        int
            The expanded samplerate of the recording.
        """
        return int(self.samplerate / self.time_expansion)

    @abstractmethod  # pragma: no cover
    def generate_recording(
        self,
        path: Path,
        duration: float | None = None,
    ) -> None:
        """Generate an audio recording.

        This method is called by the `record` method to generate the actual
        audio recording. It should be implemented by subclasses.

        Parameters
        ----------
        path : Path
            The path where to store the recording.
        """
        ...

    def check(self):
        """Check if the audio recorder is compatible with the config."""
        check_duration = 0.1

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "recording.wav"

            try:
                self.generate_recording(path=path, duration=check_duration)
            except (
                DeviceConfigurationError,
                DeviceUnavailableError,
                RecordingError,
            ) as error:
                help_text = f" Help: {error.help}" if error.help else ""
                raise HealthCheckError(
                    message=f"{error}{help_text}"
                ) from error

            if not path.exists():
                raise HealthCheckError(
                    message="No audio file was recorded during the health check."
                )

            media_info = get_media_info(path)
            if media_info.samplerate != self.samplerate:
                raise HealthCheckError(
                    message=(
                        "Recorded audio samplerate does not match the configured "
                        f"samplerate. Expected {self.samplerate} Hz, got "
                        f"{media_info.samplerate} Hz."
                    )
                )

            if media_info.audio_channels != self.audio_channels:
                raise HealthCheckError(
                    message=(
                        "Recorded audio channel count does not match the configured "
                        f"number of channels. Expected {self.audio_channels}, got "
                        f"{media_info.audio_channels}."
                    )
                )

            if not isclose(media_info.duration, check_duration, abs_tol=0.01):
                raise HealthCheckError(
                    message=(
                        "Recorded audio duration does not match the health check "
                        f"duration. Expected about {check_duration:.2f}s, got "
                        f"{media_info.duration:.2f}s."
                    )
                )


def iter_riff_chunks(fp: BinaryIO):
    fp.seek(12)

    while True:
        chunk_header = fp.read(8)

        if len(chunk_header) < 8:
            break

        chunk_id, chunk_size = struct.unpack("<4sI", chunk_header)
        yield chunk_id
        chunk_size = chunk_size + (chunk_size % 2)
        fp.seek(chunk_size, 1)


def get_media_info(path: Path) -> MediaInfo:
    """Get information about the media."""
    with wave.open(str(path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        channels = wf.getnchannels()
        return MediaInfo(
            duration=frames / rate,
            samplerate=rate,
            audio_channels=channels,
            frames=frames,
        )


def patch_samplerate(filepath: Path, new_sample_rate: int) -> None:
    with open(filepath, "r+b") as f:
        riff_header = f.read(12)

        if (
            len(riff_header) < 12
            or riff_header[0:4] != b"RIFF"
            or riff_header[8:12] != b"WAVE"
        ):
            raise ValueError("Not a valid RIFF/WAVE file.")

        for chunk_id in iter_riff_chunks(f):
            if chunk_id == b"fmt ":
                break
        else:
            raise ValueError("Could not find 'fmt ' chunk in the WAV file.")

        fmt_offset = f.tell()

        # Patch SampleRate
        f.seek(fmt_offset + 4)
        f.write(struct.pack("<I", new_sample_rate))

        # Patch ByteRate
        f.seek(fmt_offset + 12)
        block_align = struct.unpack("<H", f.read(2))[0]
        new_byte_rate = new_sample_rate * block_align
        f.seek(fmt_offset + 8)
        f.write(struct.pack("<I", new_byte_rate))
