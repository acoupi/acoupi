"""Test suite for the file management task generator."""

import datetime
import shutil
from pathlib import Path
from typing import List, Optional, Tuple
from uuid import UUID

import pytest

from acoupi import data
from acoupi.components.types import (
    RecordingSavingFilter,
    RecordingSavingManager,
    Store,
)
from acoupi.tasks import generate_file_management_task


class DummyStore(Store):
    def __init__(
        self,
        data: List[Tuple[data.Recording, List[data.ModelOutput]]],
        deployment: data.Deployment,
    ):
        self.data = data
        self.deployment = deployment

    def get_current_deployment(self) -> data.Deployment:
        return self.deployment

    def store_deployment(self, deployment: data.Deployment) -> None:
        pass

    def update_deployment(self, deployment: data.Deployment) -> None:
        pass

    def store_recording(
        self,
        recording: data.Recording,
        deployment: Optional[data.Deployment] = None,
    ) -> None:
        pass

    def store_model_output(self, model_output: data.ModelOutput) -> None:
        pass

    def get_recordings(
        self, ids: Optional[List[UUID]] = None
    ) -> List[Tuple[data.Recording, List[data.ModelOutput]]]:
        return self.data

    def get_recordings_by_path(
        self,
        paths: List[Path],
    ) -> List[Tuple[data.Recording, List[data.ModelOutput]]]:
        return self.data

    def update_recording_path(
        self, recording: data.Recording, path: Path
    ) -> data.Recording:
        return recording


class DummyRecordingManager(RecordingSavingManager):
    def __init__(self, path: Path):
        self.path = path
        if not self.path.exists():
            self.path.mkdir(parents=True)

    def save_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
    ) -> Optional[Path]:
        if recording.path is None:
            raise ValueError("Recording has no path")

        new_path = self.path / recording.path.name
        return shutil.move(recording.path, new_path)


class DummyFileFilter(RecordingSavingFilter):
    def should_save_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
    ) -> bool:
        return False


@pytest.fixture
def temp_audio_dir(tmp_path: Path) -> Path:
    return tmp_path / "tmp_audio"


@pytest.fixture
def recording(tmp_path: Path, deployment: data.Deployment) -> data.Recording:
    recording_path = tmp_path / "test.wav"
    recording_path.touch()
    return data.Recording(
        path=recording_path,
        duration=1,
        samplerate=256000,
        audio_channels=1,
        datetime=datetime.datetime.now(),
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
def target_dir(tmp_path: Path) -> Path:
    return tmp_path / "target_dir"


@pytest.fixture
def dummy_manager(target_dir: Path) -> DummyRecordingManager:
    return DummyRecordingManager(target_dir)


def test_file_management_task_keeps_unprocessed_recordings(
    recording: data.Recording,
    temp_audio_dir: Path,
    deployment: data.Deployment,
    dummy_manager: DummyRecordingManager,
):
    store = DummyStore(data=[(recording, [])], deployment=deployment)

    task = generate_file_management_task(
        store=store,
        file_managers=[dummy_manager],
        temp_path=temp_audio_dir,
        required_models=["test_model"],
    )

    task()

    assert recording.path is not None
    assert recording.path.exists()


def test_file_management_moves_files_if_no_required_model(
    target_dir: Path,
    recording: data.Recording,
    temp_audio_dir: Path,
    deployment: data.Deployment,
    dummy_manager: DummyRecordingManager,
):
    store = DummyStore(data=[(recording, [])], deployment=deployment)

    task = generate_file_management_task(
        store=store,
        file_managers=[dummy_manager],
        temp_path=temp_audio_dir,
    )

    task()

    assert recording.path is not None
    assert recording.path.exists()


def test_file_management_ignores_files_without_path(
    temp_audio_dir: Path,
    dummy_manager: DummyRecordingManager,
    deployment: data.Deployment,
):
    store = DummyStore(
        data=[
            (
                data.Recording(
                    path=None,
                    duration=1,
                    samplerate=256000,
                    datetime=datetime.datetime.now(),
                    deployment=deployment,
                ),
                [],
            )
        ],
        deployment=deployment,
    )

    task = generate_file_management_task(
        store=store,
        file_managers=[dummy_manager],
        temp_path=temp_audio_dir,
    )

    task()


def test_file_management_deletes_files_that_do_not_pass_filters(
    target_dir: Path,
    recording: data.Recording,
    temp_audio_dir: Path,
    deployment: data.Deployment,
    model_output: data.ModelOutput,
    dummy_manager: DummyRecordingManager,
):
    store = DummyStore(data=[(recording, [model_output])], deployment=deployment)

    task = generate_file_management_task(
        store=store,
        file_managers=[dummy_manager],
        temp_path=temp_audio_dir,
        file_filters=[DummyFileFilter()],
    )

    task()

    assert not recording.path.exists()
    assert not (target_dir / recording.path.name).exists()
