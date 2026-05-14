import wave
from pathlib import Path
from typing import Optional

from guano import GuanoFile


def create_wav_file(
    path: Path,
    samplerate: int = 16000,
) -> Path:
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(samplerate)
        wav_file.writeframes(b"\x00\x00" * samplerate)

    return path


def write_guano_chunk(path: Path, metadata: str) -> None:
    g = GuanoFile(str(path))
    g["Note"] = metadata
    g.write()


def read_guano_chunk(path: Path) -> Optional[str]:
    g = GuanoFile(str(path))
    return g.get("Note")
