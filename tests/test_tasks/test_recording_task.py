"""Test suite for the recording task generator."""

import datetime
import sys
from pathlib import Path

from guano import GuanoFile

from tests.test_tasks.conftest import create_wav_file

from acoupi import data
from acoupi.components import SqliteStore
from acoupi.components.types import AudioRecorder
from acoupi.tasks import generate_recording_task

if sys.version_info < (3, 10):
    from importlib_metadata import version
else:
    from importlib.metadata import version


class DummyRecorder(AudioRecorder):
    def __init__(
        self,
        path: Path,
        created_on: datetime.datetime,
        samplerate: int = 16000,
        duration: float = 1.0,
    ):
        self.path = path
        self.created_on = created_on
        self.samplerate = samplerate
        self.duration = duration

    def record(self, deployment: data.Deployment) -> data.Recording:
        create_wav_file(self.path, samplerate=self.samplerate)
        return data.Recording(
            path=self.path,
            created_on=self.created_on,
            duration=self.duration,
            samplerate=self.samplerate,
            audio_channels=1,
            chunksize=1024,
            deployment=deployment,
        )


def test_recording_task_writes_guano_metadata_with_location(
    tmp_path: Path,
    mocker,
):
    mocker.patch(
        "acoupi.tasks.recording.get_rpi_serial_number",
        return_value="1234567890ABCDEF",
    )

    deployment = data.Deployment(
        name="field-site-a",
        latitude=51.5072,
        longitude=-0.1276,
        started_on=datetime.datetime(2024, 1, 1, 0, 0, 0),
    )
    created_on = datetime.datetime(2024, 8, 4, 5, 6, 7)

    store = SqliteStore(tmp_path / "metadata.db")
    store.store_deployment(deployment)

    recorder = DummyRecorder(
        path=tmp_path / "recording.wav",
        created_on=created_on,
    )

    task = generate_recording_task(recorder=recorder, store=store)

    recording = task()

    assert recording is not None
    assert recording.path is not None

    g = GuanoFile(str(recording.path))

    assert g["GUANO|Version"] == "1.0"
    assert g["Timestamp"] == created_on
    assert g["Acoupi|Deployment Name"] == deployment.name
    assert g["Loc Position"] == (deployment.latitude, deployment.longitude)
    assert g["Firmware Version"] == version("acoupi")
    assert g["Make"] == "acoupi"
    assert g["Serial"] == "1234567890ABCDEF"


def test_recording_task_writes_guano_metadata_without_location(
    tmp_path: Path,
    mocker,
):
    mocker.patch(
        "acoupi.tasks.recording.get_rpi_serial_number",
        return_value="1234567890ABCDEF",
    )

    deployment = data.Deployment(
        name="field-site-b",
        started_on=datetime.datetime(2024, 1, 1, 0, 0, 0),
    )
    created_on = datetime.datetime(2024, 8, 4, 5, 6, 7)

    store = SqliteStore(tmp_path / "metadata.db")
    store.store_deployment(deployment)

    recorder = DummyRecorder(
        path=tmp_path / "recording.wav",
        created_on=created_on,
    )

    task = generate_recording_task(recorder=recorder, store=store)

    recording = task()

    assert recording is not None
    assert recording.path is not None

    g = GuanoFile(str(recording.path))

    assert g["GUANO|Version"] == "1.0"
    assert g["Timestamp"] == created_on
    assert g["Acoupi|Deployment Name"] == deployment.name
    assert "Loc Position" not in g, g["Loc Position"]
