"""Test suite for the file management task generator."""

import datetime
from pathlib import Path
from typing import List, Optional

import pytest

from acoupi import data
from acoupi.components import SqliteStore
from acoupi.components.types import (
    RecordingSavingFilter,
    RecordingSavingManager,
)
from acoupi.tasks import generate_file_management_task


class DummyRecordingManager(RecordingSavingManager):
    def __init__(self, path: Path):
        self.path = path
        if not self.path.exists():
            self.path.mkdir(parents=True)

    def save_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
    ) -> Path:
        if recording.path is None:
            raise ValueError("Recording has no path")

        return self.path / recording.path.name


class DummyFileFilter(RecordingSavingFilter):
    def should_save_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
    ) -> bool:
        return False


@pytest.fixture
def temp_audio_dir(tmp_path: Path) -> Path:
    path = tmp_path / "tmp_audio"
    if not path.exists():
        path.mkdir()
    return path


@pytest.fixture
def recording(
    temp_audio_dir: Path, deployment: data.Deployment
) -> data.Recording:
    recording_path = temp_audio_dir / "test.wav"
    recording_path.touch()
    return data.Recording(
        path=recording_path,
        duration=1,
        samplerate=256000,
        audio_channels=1,
        created_on=datetime.datetime.now(),
        deployment=deployment,
    )


@pytest.fixture
def model_output(recording: data.Recording) -> data.ModelOutput:
    return data.ModelOutput(
        name_model="test_model",
        recording=recording,
        tags=[
            data.PredictedTag(
                tag=data.Tag(key="test", value="value1"),
                confidence_score=0.8,
            ),
            data.PredictedTag(
                tag=data.Tag(key="test", value="value2"),
                confidence_score=0.8,
            ),
        ],
        detections=[
            data.Detection(
                location=data.BoundingBox(coordinates=(1, 1000, 2, 2000)),
                detection_score=0.6,
                tags=[
                    data.PredictedTag(
                        tag=data.Tag(key="test2", value="value3"),
                        confidence_score=0.3,
                    ),
                    data.PredictedTag(
                        tag=data.Tag(key="test", value="value1"),
                        confidence_score=0.2,
                    ),
                ],
            )
        ],
    )


@pytest.fixture
def store(tmp_path: Path, deployment: data.Deployment) -> SqliteStore:
    store = SqliteStore(tmp_path / "test.db")
    store.store_deployment(deployment)
    return store


@pytest.fixture
def target_dir(tmp_path: Path) -> Path:
    return tmp_path / "target_dir"


@pytest.fixture
def dummy_manager(target_dir: Path) -> DummyRecordingManager:
    return DummyRecordingManager(target_dir)


def test_file_management_task_keeps_unprocessed_recordings(
    recording: data.Recording,
    temp_audio_dir: Path,
    dummy_manager: DummyRecordingManager,
    store: SqliteStore,
):
    store.store_recording(recording)

    task = generate_file_management_task(
        store=store,
        file_managers=[dummy_manager],
        tmp_path=temp_audio_dir,
        required_models=["test_model"],
    )

    task()

    assert recording.path is not None
    assert recording.path.exists()


def test_file_management_moves_files_if_no_required_model(
    target_dir: Path,
    recording: data.Recording,
    temp_audio_dir: Path,
    dummy_manager: DummyRecordingManager,
    store: SqliteStore,
):
    store.store_recording(recording)

    task = generate_file_management_task(
        store=store,
        file_managers=[dummy_manager],
        tmp_path=temp_audio_dir,
    )

    task()

    recording, _ = store.get_recordings([recording.id])[0]
    assert recording.path is not None
    assert recording.path.exists()
    assert recording.path.is_relative_to(target_dir)


def test_file_management_ignores_files_without_path(
    temp_audio_dir: Path,
    dummy_manager: DummyRecordingManager,
    deployment: data.Deployment,
    store: SqliteStore,
):
    recording = data.Recording(
        path=None,
        duration=1,
        samplerate=256000,
        created_on=datetime.datetime.now(),
        deployment=deployment,
    )
    store.store_recording(recording)
    task = generate_file_management_task(
        store=store,
        file_managers=[dummy_manager],
        tmp_path=temp_audio_dir,
    )

    task()


def test_file_management_deletes_files_that_do_not_pass_filters(
    target_dir: Path,
    recording: data.Recording,
    temp_audio_dir: Path,
    model_output: data.ModelOutput,
    dummy_manager: DummyRecordingManager,
    store: SqliteStore,
):
    store.store_recording(recording)
    store.store_model_output(model_output)

    task = generate_file_management_task(
        store=store,
        file_managers=[dummy_manager],
        tmp_path=temp_audio_dir,
        file_filters=[DummyFileFilter()],
    )

    task()

    assert recording.path is not None
    assert not recording.path.exists()
    assert not (target_dir / recording.path.name).exists()
