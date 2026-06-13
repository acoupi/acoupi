"""Test suite for the file management task generator."""

from pathlib import Path
from typing import List, Optional, Sequence

import pytest

from tests.test_tasks.conftest import (
    create_wav_file,
    read_guano_chunk,
    write_guano_chunk,
)

from acoupi import data
from acoupi.components import SqliteStore
from acoupi.components.types import (
    RecordingSavingFilter,
    RecordingSavingManager,
)
from acoupi.tasks import generate_file_management_task


def always_manage(
    recording: data.Recording,
    model_outputs: Sequence[data.ModelOutputInfo],
) -> bool:
    return True


def never_manage(
    recording: data.Recording,
    model_outputs: Sequence[data.ModelOutputInfo],
) -> bool:
    return False


def manage_if_any_model_output(
    recording: data.Recording,
    model_outputs: Sequence[data.ModelOutputInfo],
) -> bool:
    return bool(model_outputs)


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
        created_on=data.utc_now(),
        deployment=deployment,
    )


@pytest.fixture
def model_output(recording: data.Recording) -> data.ModelOutput:
    return data.ModelOutput(
        name_model="test_model",
        recording=recording,
        detections=[
            data.PresenceDetection(
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
        created_on=data.utc_now(),
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


def test_file_management_preserves_existing_guano_metadata(
    target_dir: Path,
    temp_audio_dir: Path,
    dummy_manager: DummyRecordingManager,
    deployment: data.Deployment,
    store: SqliteStore,
):
    recording_path = temp_audio_dir / "test.wav"
    create_wav_file(recording_path)
    write_guano_chunk(recording_path, "Hi from acoupi!")

    recording = data.Recording(
        path=recording_path,
        duration=1,
        samplerate=16000,
        audio_channels=1,
        created_on=data.utc_now(),
        deployment=deployment,
    )
    store.store_recording(recording)

    task = generate_file_management_task(
        store=store,
        file_managers=[dummy_manager],
        tmp_path=temp_audio_dir,
    )

    task()

    saved_recording, _ = store.get_recordings([recording.id])[0]
    assert saved_recording.path is not None
    assert saved_recording.path.exists()
    assert saved_recording.path.is_relative_to(target_dir)
    guano_text = read_guano_chunk(saved_recording.path)
    assert guano_text is not None
    assert "Hi from acoupi!" in guano_text


def test_file_management_moves_files_when_conditions_are_met(
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
        management_conditions=[always_manage],
    )

    task()

    # Then
    recording, _ = store.get_recordings([recording.id])[0]
    assert recording.path is not None
    assert recording.path.exists()
    assert recording.path.is_relative_to(target_dir)


def test_file_management_keeps_recordings_when_condition_fails(
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
        management_conditions=[never_manage],
    )

    task()

    assert recording.path is not None
    assert recording.path.exists()
    assert recording.path.is_relative_to(temp_audio_dir)


def test_file_management_moves_files_when_all_conditions_pass(
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
        management_conditions=[always_manage, manage_if_any_model_output],
    )

    task()

    recording, _ = store.get_recordings([recording.id])[0]
    assert recording.path is not None
    assert recording.path.exists()
    assert recording.path.is_relative_to(target_dir)


def test_file_management_keeps_recordings_when_one_condition_fails(
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
        management_conditions=[always_manage, never_manage],
    )

    task()

    assert recording.path is not None
    assert recording.path.exists()
    assert recording.path.is_relative_to(temp_audio_dir)


def test_file_management_moves_files_when_models_and_conditions_pass(
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
        required_models=["test_model"],
        management_conditions=[always_manage],
    )

    task()

    recording, _ = store.get_recordings([recording.id])[0]
    assert recording.path is not None
    assert recording.path.exists()
    assert recording.path.is_relative_to(target_dir)


def test_file_management_keeps_recordings_when_models_pass_but_condition_fails(
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
        required_models=["test_model"],
        management_conditions=[never_manage],
    )

    task()

    assert recording.path is not None
    assert recording.path.exists()
    assert recording.path.is_relative_to(temp_audio_dir)
