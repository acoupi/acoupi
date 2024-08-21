"""Test acoupi components saving managers."""

import datetime
from pathlib import Path
from typing import List

import pytest

from acoupi import data
from acoupi.components import saving_managers


@pytest.fixture
def create_test_recording():
    """Fixture for creating random recording.

    Will create a recording with a path, duration, samplerate, deployment and datetime.
    """
    deployment = data.Deployment(
        name="test_deployment",
    )

    def factory(
        recording_time: datetime.datetime,
        recording_path: Path,
        duration: float = 1,
        samplerate: int = 256000,
        audio_channels: int = 1,
    ) -> data.Recording:
        """Return a recording."""
        return data.Recording(
            path=recording_path,
            duration=duration,
            samplerate=samplerate,
            audio_channels=audio_channels,
            deployment=deployment,
            datetime=recording_time,
        )

    return factory


@pytest.fixture
def create_test_detection():
    """Fixture for creating random detections.

    Will create detections with no location and a single tag.
    """

    def factory(
        tag_value: str,
        tag_key: str = "species",
        classification_probability: float = 0.4,
        detection_probability: float = 0.8,
    ) -> data.Detection:
        """Return a random detection."""
        return data.Detection(
            detection_probability=detection_probability,
            tags=[
                data.PredictedTag(
                    tag=data.Tag(
                        value=tag_value,
                        key=tag_key,
                    ),
                    classification_probability=classification_probability,
                ),
            ],
        )

    return factory


@pytest.fixture
def create_test_model_output():
    """Fixture for creating random model output."""
    deployment = data.Deployment(
        name="test_deployment",
    )

    recording = data.Recording(
        path=Path(),
        duration=1,
        samplerate=256000,
        audio_channels=1,
        deployment=deployment,
        datetime=datetime.datetime.now(),
    )

    def factory(
        detections: List[data.Detection],
    ) -> data.ModelOutput:
        """Return a model output."""
        return data.ModelOutput(
            recording=recording,
            name_model="test_model",
            detections=detections,
        )

    return factory


def test_save_recording_manager_fails_if_recording_has_no_path(
    tmp_path: Path,
    create_test_recording,
):
    saving_manager = saving_managers.SaveRecordingManager(tmp_path)
    recording = create_test_recording(
        recording_path=None,
        recording_time=datetime.datetime(2020, 1, 1, 0, 0, 0),
    )
    with pytest.raises(ValueError):
        saving_manager.update_recording_path(recording)


def test_save_recording_with_confident_detections(
    tmp_path: Path,
    create_test_recording,
    create_test_detection,
    create_test_model_output,
) -> None:
    """Test saving a recording with confident detections."""
    # Setup
    detection_threshold = 0.7
    saving_threshold = 0.6
    tmp_audio_dirpath = tmp_path / "audio"
    tmp_dirpath_true = tmp_audio_dirpath / "true_detections"
    tmp_dirpath_false = tmp_audio_dirpath / "false_detections"
    tmp_audio_dirpath.mkdir()
    tmp_dirpath_true.mkdir()
    tmp_dirpath_false.mkdir()

    recording_file = tmp_path / "test_recording.wav"
    recording_file.touch()
    recording_file.write_text("test recording in true_detections folder")

    recording = create_test_recording(
        recording_time=datetime.datetime(2020, 1, 1, 0, 0, 0),
        recording_path=recording_file,
    )

    model_output = create_test_model_output(
        detections=[
            create_test_detection(
                tag_value="species_1",
                classification_probability=0.6,
                detection_probability=0.8,
            ),
        ]
    )

    saving_manager = saving_managers.SaveRecordingManager(
        dirpath=tmp_audio_dirpath,
        dirpath_true=tmp_dirpath_true,
        dirpath_false=tmp_dirpath_false,
        timeformat="%Y%m%d%H%M%S",
        detection_threshold=detection_threshold,
        saving_threshold=saving_threshold,
    )

    # Run
    new_path = saving_manager.update_recording_path(
        recording, model_outputs=[model_output]
    )

    # assert
    assert not recording_file.exists()
    assert new_path.exists()
    assert new_path.parent == saving_manager.dirpath_true
    assert new_path.read_text() == "test recording in true_detections folder"


def test_save_recording_with_unconfident_detections(
    tmp_path: Path,
    create_test_recording,
    create_test_detection,
    create_test_model_output,
) -> None:
    """Test saving a recording with confident detections."""
    # Setup
    detection_threshold = 0.7
    saving_threshold = 0.4
    tmp_audio_dirpath = tmp_path / "audio"
    tmp_dirpath_true = tmp_audio_dirpath / "true_detections"
    tmp_dirpath_false = tmp_audio_dirpath / "false_detections"
    tmp_audio_dirpath.mkdir()
    tmp_dirpath_true.mkdir()
    tmp_dirpath_false.mkdir()

    recording_file = tmp_path / "test_recording.wav"
    recording_file.touch()
    recording_file.write_text(
        "test recording going to false_detections folder"
    )

    recording = create_test_recording(
        recording_time=datetime.datetime(2020, 1, 1, 0, 0, 0),
        recording_path=recording_file,
    )
    model_output = create_test_model_output(
        detections=[
            create_test_detection(
                tag_value="species_1",
                classification_probability=0.5,
                detection_probability=0.6,
            ),
        ]
    )

    saving_manager = saving_managers.SaveRecordingManager(
        dirpath=tmp_audio_dirpath,
        dirpath_true=tmp_dirpath_true,
        dirpath_false=tmp_dirpath_false,
        timeformat="%Y%m%d%H%M%S",
        detection_threshold=detection_threshold,
        saving_threshold=saving_threshold,
    )

    # Run
    new_path = saving_manager.update_recording_path(
        recording, model_outputs=[model_output]
    )

    # Assert
    assert not recording_file.exists()
    assert new_path.exists()
    assert new_path.parent == saving_manager.dirpath_false
    assert (
        new_path.read_text()
        == "test recording going to false_detections folder"
    )


def test_delete_recordings(
    tmp_path: Path,
    create_test_recording,
    create_test_detection,
    create_test_model_output,
) -> None:
    """Test saving a recording with confident detections."""
    # Setup
    detection_threshold = 0.7
    saving_threshold = 0.4
    tmp_audio_dirpath = tmp_path / "audio"
    tmp_dirpath_true = tmp_audio_dirpath / "true_detections"
    tmp_dirpath_false = tmp_audio_dirpath / "false_detections"
    tmp_audio_dirpath.mkdir()
    tmp_dirpath_true.mkdir()
    tmp_dirpath_false.mkdir()

    recording_file = tmp_path / "test_recording.wav"
    recording_file.touch()
    recording_file.write_text("test recording going to right folder")

    recording = create_test_recording(
        recording_time=datetime.datetime(2020, 1, 1, 0, 0, 0),
        recording_path=recording_file,
    )

    model_output = create_test_model_output(
        detections=[
            create_test_detection(
                tag_value="species_1",
                classification_probability=0.2,
                detection_probability=0.3,
            ),
        ]
    )

    saving_manager = saving_managers.SaveRecordingManager(
        dirpath=tmp_audio_dirpath,
        dirpath_true=tmp_dirpath_true,
        dirpath_false=tmp_dirpath_false,
        timeformat="%Y%m%d%H%M%S",
        detection_threshold=detection_threshold,
        saving_threshold=saving_threshold,
    )

    # Run
    new_path = saving_manager.update_recording_path(
        recording, model_outputs=[model_output]
    )

    # Assert
    assert new_path == None
    assert not recording_file.exists()


def test_date_file_manager_save_recording(
    tmp_path: Path,
    create_test_recording,
):
    """Test DateFileManager.update_recording_path."""
    # Setup
    tmp_audio_dirpath = tmp_path / "audio"
    tmp_audio_dirpath.mkdir()
    recording_file = tmp_path / "test_recording.wav"
    recording_file.touch()

    recording = create_test_recording(
        recording_time=datetime.datetime(2024, 8, 1, 20, 30, 0),
        recording_path=recording_file,
    )

    # create a saving manager
    file_saving_manager = saving_managers.DateFileManager(
        directory=tmp_audio_dirpath,
    )

    # Run
    file_path = file_saving_manager.get_file_path(recording)

    # Assert
    assert tmp_audio_dirpath.exists()
    assert file_path == Path("2024") / "8" / "1" / f"203000_{recording.id}.wav"
