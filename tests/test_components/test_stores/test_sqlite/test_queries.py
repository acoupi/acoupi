"""Test sqlite metadata query helpers."""

import datetime
import sqlite3
import uuid
from pathlib import Path

import pytest

from acoupi import data
from acoupi.components.stores.sqlite import queries
from acoupi.components.stores.sqlite.database import create_base_schema
from acoupi.system.database import connect_db


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """Given a temporary sqlite database path."""
    return tmp_path / "queries.db"


@pytest.fixture
def db_connection(db_path: Path):
    """Given a sqlite connection with the metadata schema initialised."""
    with connect_db(db_path) as connection:
        create_base_schema(connection)
        yield connection


def build_recording(
    deployment: data.Deployment,
    *,
    path: str,
    created_on: datetime.datetime,
) -> data.Recording:
    return data.Recording(
        deployment=deployment,
        path=Path(path),
        duration=1.0,
        samplerate=16000,
        created_on=created_on,
    )


def build_model_output(
    recording: data.Recording,
    *,
    name_model: str,
    created_on: datetime.datetime,
    file_tag: tuple[str, str, float],
    detection_score: float,
    detection_tag: tuple[str, str, float],
) -> data.ModelOutput:
    file_key, file_value, file_score = file_tag
    detection_key, detection_value, detection_tag_score = detection_tag

    return data.ModelOutput(
        id=uuid.uuid4(),
        name_model=name_model,
        recording=recording,
        created_on=created_on,
        tags=[
            data.PredictedTag(
                tag=data.Tag(key=file_key, value=file_value),
                confidence_score=file_score,
            )
        ],
        detections=[
            data.Detection(
                id=uuid.uuid4(),
                location=data.BoundingBox(coordinates=(1, 1000, 2, 2000)),
                detection_score=detection_score,
                tags=[
                    data.PredictedTag(
                        tag=data.Tag(
                            key=detection_key,
                            value=detection_value,
                        ),
                        confidence_score=detection_tag_score,
                    )
                ],
            )
        ],
    )


class TestCreateDeployment:
    def test_stores_row(
        self,
        db_connection: sqlite3.Connection,
        deployment: data.Deployment,
    ) -> None:
        # Given a fresh database connection

        # When creating and reading the deployment
        queries.create_deployment(db_connection, deployment)
        retrieved = queries.get_deployment_by_id(db_connection, deployment.id)

        # Then the stored deployment is returned intact
        assert retrieved == deployment


class TestGetDeploymentById:
    def test_raises_for_unknown_id(
        self,
        db_connection: sqlite3.Connection,
    ) -> None:
        # Given an empty database connection
        # When / Then reading an unknown deployment fails
        with pytest.raises(ValueError, match="No deployment found"):
            queries.get_deployment_by_id(db_connection, uuid.uuid4())


class TestGetRecordingsByIds:
    def test_returns_recordings_in_descending_datetime_order(
        self,
        db_connection: sqlite3.Connection,
        deployment: data.Deployment,
    ) -> None:
        first = data.Recording(
            deployment=deployment,
            path=Path("first.wav"),
            duration=1.0,
            samplerate=16000,
            created_on=datetime.datetime.now(),
        )
        second = first.model_copy(
            update=dict(
                id=uuid.uuid4(),
                path=Path("second.wav"),
                created_on=first.created_on + datetime.timedelta(seconds=5),
            )
        )

        # Given a deployment and two stored recordings
        queries.create_deployment(db_connection, deployment)
        queries.create_recording(db_connection, first, deployment)
        queries.create_recording(db_connection, second, deployment)

        # When reading both recordings by id
        retrieved = queries.get_recordings_by_ids(
            db_connection,
            [first.id, second.id],
        )

        # Then the newest recording is returned first
        assert retrieved == [second, first]


class TestGetRecordingsModelOutputs:
    def test_returns_outputs_grouped_by_recording(
        self,
        db_connection: sqlite3.Connection,
        deployment: data.Deployment,
        recording: data.Recording,
        model_output: data.ModelOutput,
    ) -> None:
        # Given a seeded database connection
        queries.create_deployment(db_connection, deployment)
        queries.create_recording(db_connection, recording, deployment)
        queries.insert_model_outputs(db_connection, [model_output])

        # When reading outputs for one recording
        retrieved = queries.get_recordings_model_outputs(
            db_connection,
            {recording.id: recording},
        )

        # Then the outputs are grouped under that recording id
        assert retrieved == {recording.id: [model_output]}


class TestGetModelOutputs:
    def test_filters_by_model_name(
        self,
        db_connection: sqlite3.Connection,
        deployment: data.Deployment,
        recording: data.Recording,
        model_output: data.ModelOutput,
    ) -> None:
        # Given a seeded database connection
        queries.create_deployment(db_connection, deployment)
        queries.create_recording(db_connection, recording, deployment)
        queries.insert_model_outputs(db_connection, [model_output])

        # When filtering model outputs by model name
        retrieved = queries.get_model_outputs(
            db_connection,
            model_names=[model_output.name_model],
        )

        # Then the matching model output is returned
        assert retrieved == [model_output]

    def test_filters_by_id(
        self,
        db_connection: sqlite3.Connection,
        deployment: data.Deployment,
    ) -> None:
        base_time = datetime.datetime.now(datetime.timezone.utc)
        first_recording = build_recording(
            deployment,
            path="first.wav",
            created_on=base_time,
        )
        second_recording = build_recording(
            deployment,
            path="second.wav",
            created_on=base_time + datetime.timedelta(seconds=10),
        )
        first_output = build_model_output(
            first_recording,
            name_model="test_model",
            created_on=base_time,
            file_tag=("test", "value1", 0.8),
            detection_score=0.6,
            detection_tag=("test2", "value3", 0.3),
        )
        second_output = build_model_output(
            second_recording,
            name_model="other_model",
            created_on=base_time + datetime.timedelta(seconds=10),
            file_tag=("site", "second", 0.5),
            detection_score=0.2,
            detection_tag=("species", "other", 0.1),
        )

        queries.create_deployment(db_connection, deployment)
        queries.create_recording(db_connection, first_recording, deployment)
        queries.insert_model_outputs(db_connection, [first_output])
        queries.create_recording(db_connection, second_recording, deployment)
        queries.insert_model_outputs(db_connection, [second_output])

        # When filtering model outputs by id
        retrieved = queries.get_model_outputs(
            db_connection, ids=[first_output.id]
        )

        # Then only the requested output is returned
        assert retrieved == [first_output]

    def test_filters_by_recording_id(
        self,
        db_connection: sqlite3.Connection,
        deployment: data.Deployment,
    ) -> None:
        base_time = datetime.datetime.now(datetime.timezone.utc)
        first_recording = build_recording(
            deployment,
            path="first.wav",
            created_on=base_time,
        )
        second_recording = build_recording(
            deployment,
            path="second.wav",
            created_on=base_time + datetime.timedelta(seconds=10),
        )
        first_output = build_model_output(
            first_recording,
            name_model="test_model",
            created_on=base_time,
            file_tag=("test", "value1", 0.8),
            detection_score=0.6,
            detection_tag=("test2", "value3", 0.3),
        )
        second_output = build_model_output(
            second_recording,
            name_model="other_model",
            created_on=base_time + datetime.timedelta(seconds=10),
            file_tag=("site", "second", 0.5),
            detection_score=0.2,
            detection_tag=("species", "other", 0.1),
        )

        queries.create_deployment(db_connection, deployment)
        queries.create_recording(db_connection, first_recording, deployment)
        queries.insert_model_outputs(db_connection, [first_output])
        queries.create_recording(db_connection, second_recording, deployment)
        queries.insert_model_outputs(db_connection, [second_output])

        # When filtering model outputs by recording id
        retrieved = queries.get_model_outputs(
            db_connection,
            recording_ids=[first_recording.id],
        )

        # Then only outputs for that recording are returned
        assert retrieved == [first_output]

    def test_filters_by_detection_id(
        self,
        db_connection: sqlite3.Connection,
        deployment: data.Deployment,
    ) -> None:
        base_time = datetime.datetime.now(datetime.timezone.utc)
        first_recording = build_recording(
            deployment,
            path="first.wav",
            created_on=base_time,
        )
        second_recording = build_recording(
            deployment,
            path="second.wav",
            created_on=base_time + datetime.timedelta(seconds=10),
        )
        first_output = build_model_output(
            first_recording,
            name_model="test_model",
            created_on=base_time,
            file_tag=("test", "value1", 0.8),
            detection_score=0.6,
            detection_tag=("test2", "value3", 0.3),
        )
        second_output = build_model_output(
            second_recording,
            name_model="other_model",
            created_on=base_time + datetime.timedelta(seconds=10),
            file_tag=("site", "second", 0.5),
            detection_score=0.2,
            detection_tag=("species", "other", 0.1),
        )

        queries.create_deployment(db_connection, deployment)
        queries.create_recording(db_connection, first_recording, deployment)
        queries.insert_model_outputs(db_connection, [first_output])
        queries.create_recording(db_connection, second_recording, deployment)
        queries.insert_model_outputs(db_connection, [second_output])

        detection_id = first_output.detections[0].id

        # When filtering model outputs by detection id
        retrieved = queries.get_model_outputs(
            db_connection,
            detection_ids=[detection_id],
        )

        # Then only the output containing that detection is returned
        assert retrieved == [first_output]

    def test_filters_by_after_datetime(
        self,
        db_connection: sqlite3.Connection,
        deployment: data.Deployment,
    ) -> None:
        base_time = datetime.datetime.now(datetime.timezone.utc)
        first_recording = build_recording(
            deployment,
            path="first.wav",
            created_on=base_time,
        )
        second_recording = build_recording(
            deployment,
            path="second.wav",
            created_on=base_time + datetime.timedelta(seconds=10),
        )
        first_output = build_model_output(
            first_recording,
            name_model="test_model",
            created_on=base_time,
            file_tag=("test", "value1", 0.8),
            detection_score=0.6,
            detection_tag=("test2", "value3", 0.3),
        )
        second_output = build_model_output(
            second_recording,
            name_model="other_model",
            created_on=base_time + datetime.timedelta(seconds=10),
            file_tag=("site", "second", 0.5),
            detection_score=0.2,
            detection_tag=("species", "other", 0.1),
        )

        queries.create_deployment(db_connection, deployment)
        queries.create_recording(db_connection, first_recording, deployment)
        queries.insert_model_outputs(db_connection, [first_output])
        queries.create_recording(db_connection, second_recording, deployment)
        queries.insert_model_outputs(db_connection, [second_output])

        # When filtering model outputs after the first output time
        retrieved = queries.get_model_outputs(
            db_connection,
            after=second_output.created_on,
        )

        # Then only the newer output is returned
        assert retrieved == [second_output]

    def test_filters_by_before_datetime(
        self,
        db_connection: sqlite3.Connection,
        deployment: data.Deployment,
    ) -> None:
        base_time = datetime.datetime.now(datetime.timezone.utc)
        first_recording = build_recording(
            deployment,
            path="first.wav",
            created_on=base_time,
        )
        second_recording = build_recording(
            deployment,
            path="second.wav",
            created_on=base_time + datetime.timedelta(seconds=10),
        )
        first_output = build_model_output(
            first_recording,
            name_model="test_model",
            created_on=base_time,
            file_tag=("test", "value1", 0.8),
            detection_score=0.6,
            detection_tag=("test2", "value3", 0.3),
        )
        second_output = build_model_output(
            second_recording,
            name_model="other_model",
            created_on=base_time + datetime.timedelta(seconds=10),
            file_tag=("site", "second", 0.5),
            detection_score=0.2,
            detection_tag=("species", "other", 0.1),
        )

        queries.create_deployment(db_connection, deployment)
        queries.create_recording(db_connection, first_recording, deployment)
        queries.insert_model_outputs(db_connection, [first_output])
        queries.create_recording(db_connection, second_recording, deployment)
        queries.insert_model_outputs(db_connection, [second_output])

        # When filtering model outputs before the second output time
        retrieved = queries.get_model_outputs(
            db_connection,
            before=first_output.created_on,
        )

        # Then only the older output is returned
        assert retrieved == [first_output]

    def test_respects_limit(
        self,
        db_connection: sqlite3.Connection,
        deployment: data.Deployment,
    ) -> None:
        base_time = datetime.datetime.now(datetime.timezone.utc)
        first_recording = build_recording(
            deployment,
            path="first.wav",
            created_on=base_time,
        )
        second_recording = build_recording(
            deployment,
            path="second.wav",
            created_on=base_time + datetime.timedelta(seconds=10),
        )
        first_output = build_model_output(
            first_recording,
            name_model="test_model",
            created_on=base_time,
            file_tag=("test", "value1", 0.8),
            detection_score=0.6,
            detection_tag=("test2", "value3", 0.3),
        )
        second_output = build_model_output(
            second_recording,
            name_model="other_model",
            created_on=base_time + datetime.timedelta(seconds=10),
            file_tag=("site", "second", 0.5),
            detection_score=0.2,
            detection_tag=("species", "other", 0.1),
        )

        queries.create_deployment(db_connection, deployment)
        queries.create_recording(db_connection, first_recording, deployment)
        queries.insert_model_outputs(db_connection, [first_output])
        queries.create_recording(db_connection, second_recording, deployment)
        queries.insert_model_outputs(db_connection, [second_output])

        # When limiting model outputs to one row
        retrieved = queries.get_model_outputs(db_connection, limit=1)

        # Then only the newest output is returned
        assert retrieved == [second_output]


class TestGetDetections:
    def test_filters_by_score_threshold(
        self,
        db_connection: sqlite3.Connection,
        deployment: data.Deployment,
        recording: data.Recording,
        model_output: data.ModelOutput,
    ) -> None:
        # Given a seeded database
        queries.create_deployment(db_connection, deployment)
        queries.create_recording(db_connection, recording, deployment)
        queries.insert_model_outputs(db_connection, [model_output])

        # When filtering detections by score
        retrieved = queries.get_detections(
            db_connection,
            score_gt=0.5,
        )

        # Then the detection above threshold is returned
        assert retrieved == model_output.detections

    def test_filters_by_id(
        self,
        db_connection: sqlite3.Connection,
        deployment: data.Deployment,
    ) -> None:
        base_time = datetime.datetime.now(datetime.timezone.utc)
        first_recording = build_recording(
            deployment,
            path="first.wav",
            created_on=base_time,
        )
        second_recording = build_recording(
            deployment,
            path="second.wav",
            created_on=base_time + datetime.timedelta(seconds=10),
        )
        first_output = build_model_output(
            first_recording,
            name_model="test_model",
            created_on=base_time,
            file_tag=("test", "value1", 0.8),
            detection_score=0.6,
            detection_tag=("test2", "value3", 0.3),
        )
        second_output = build_model_output(
            second_recording,
            name_model="other_model",
            created_on=base_time + datetime.timedelta(seconds=10),
            file_tag=("site", "second", 0.5),
            detection_score=0.2,
            detection_tag=("species", "other", 0.1),
        )

        queries.create_deployment(db_connection, deployment)
        queries.create_recording(db_connection, first_recording, deployment)
        queries.insert_model_outputs(db_connection, [first_output])
        queries.create_recording(db_connection, second_recording, deployment)
        queries.insert_model_outputs(db_connection, [second_output])

        detection = first_output.detections[0]

        # When filtering detections by id
        retrieved = queries.get_detections(db_connection, ids=[detection.id])

        # Then only that detection is returned
        assert retrieved == [detection]

    def test_filters_by_model_output_id(
        self,
        db_connection: sqlite3.Connection,
        deployment: data.Deployment,
    ) -> None:
        base_time = datetime.datetime.now(datetime.timezone.utc)
        first_recording = build_recording(
            deployment,
            path="first.wav",
            created_on=base_time,
        )
        second_recording = build_recording(
            deployment,
            path="second.wav",
            created_on=base_time + datetime.timedelta(seconds=10),
        )
        first_output = build_model_output(
            first_recording,
            name_model="test_model",
            created_on=base_time,
            file_tag=("test", "value1", 0.8),
            detection_score=0.6,
            detection_tag=("test2", "value3", 0.3),
        )
        second_output = build_model_output(
            second_recording,
            name_model="other_model",
            created_on=base_time + datetime.timedelta(seconds=10),
            file_tag=("site", "second", 0.5),
            detection_score=0.2,
            detection_tag=("species", "other", 0.1),
        )

        queries.create_deployment(db_connection, deployment)
        queries.create_recording(db_connection, first_recording, deployment)
        queries.insert_model_outputs(db_connection, [first_output])
        queries.create_recording(db_connection, second_recording, deployment)
        queries.insert_model_outputs(db_connection, [second_output])

        # When filtering detections by model output id
        retrieved = queries.get_detections(
            db_connection,
            model_output_ids=[first_output.id],
        )

        # Then only detections for that output are returned
        assert retrieved == first_output.detections

    def test_filters_by_score_lt(
        self,
        db_connection: sqlite3.Connection,
        deployment: data.Deployment,
    ) -> None:
        base_time = datetime.datetime.now(datetime.timezone.utc)
        first_recording = build_recording(
            deployment,
            path="first.wav",
            created_on=base_time,
        )
        second_recording = build_recording(
            deployment,
            path="second.wav",
            created_on=base_time + datetime.timedelta(seconds=10),
        )
        first_output = build_model_output(
            first_recording,
            name_model="test_model",
            created_on=base_time,
            file_tag=("test", "value1", 0.8),
            detection_score=0.6,
            detection_tag=("test2", "value3", 0.3),
        )
        second_output = build_model_output(
            second_recording,
            name_model="other_model",
            created_on=base_time + datetime.timedelta(seconds=10),
            file_tag=("site", "second", 0.5),
            detection_score=0.2,
            detection_tag=("species", "other", 0.1),
        )

        queries.create_deployment(db_connection, deployment)
        queries.create_recording(db_connection, first_recording, deployment)
        queries.insert_model_outputs(db_connection, [first_output])
        queries.create_recording(db_connection, second_recording, deployment)
        queries.insert_model_outputs(db_connection, [second_output])

        # When filtering detections below a score threshold
        retrieved = queries.get_detections(db_connection, score_lt=0.5)

        # Then only the lower-scored detection is returned
        assert retrieved == second_output.detections

    def test_filters_by_model_name(
        self,
        db_connection: sqlite3.Connection,
        deployment: data.Deployment,
    ) -> None:
        base_time = datetime.datetime.now(datetime.timezone.utc)
        first_recording = build_recording(
            deployment,
            path="first.wav",
            created_on=base_time,
        )
        second_recording = build_recording(
            deployment,
            path="second.wav",
            created_on=base_time + datetime.timedelta(seconds=10),
        )
        first_output = build_model_output(
            first_recording,
            name_model="test_model",
            created_on=base_time,
            file_tag=("test", "value1", 0.8),
            detection_score=0.6,
            detection_tag=("test2", "value3", 0.3),
        )
        second_output = build_model_output(
            second_recording,
            name_model="other_model",
            created_on=base_time + datetime.timedelta(seconds=10),
            file_tag=("site", "second", 0.5),
            detection_score=0.2,
            detection_tag=("species", "other", 0.1),
        )

        queries.create_deployment(db_connection, deployment)
        queries.create_recording(db_connection, first_recording, deployment)
        queries.insert_model_outputs(db_connection, [first_output])
        queries.create_recording(db_connection, second_recording, deployment)
        queries.insert_model_outputs(db_connection, [second_output])

        # When filtering detections by model name
        retrieved = queries.get_detections(
            db_connection,
            model_names=[second_output.name_model],
        )

        # Then only detections from that model are returned
        assert retrieved == second_output.detections

    def test_filters_by_after_datetime(
        self,
        db_connection: sqlite3.Connection,
        deployment: data.Deployment,
    ) -> None:
        base_time = datetime.datetime.now(datetime.timezone.utc)
        first_recording = build_recording(
            deployment,
            path="first.wav",
            created_on=base_time,
        )
        second_recording = build_recording(
            deployment,
            path="second.wav",
            created_on=base_time + datetime.timedelta(seconds=10),
        )
        first_output = build_model_output(
            first_recording,
            name_model="test_model",
            created_on=base_time,
            file_tag=("test", "value1", 0.8),
            detection_score=0.6,
            detection_tag=("test2", "value3", 0.3),
        )
        second_output = build_model_output(
            second_recording,
            name_model="other_model",
            created_on=base_time + datetime.timedelta(seconds=10),
            file_tag=("site", "second", 0.5),
            detection_score=0.2,
            detection_tag=("species", "other", 0.1),
        )

        queries.create_deployment(db_connection, deployment)
        queries.create_recording(db_connection, first_recording, deployment)
        queries.insert_model_outputs(db_connection, [first_output])
        queries.create_recording(db_connection, second_recording, deployment)
        queries.insert_model_outputs(db_connection, [second_output])

        # When filtering detections after the newer output time
        retrieved = queries.get_detections(
            db_connection,
            after=second_output.created_on,
        )

        # Then only detections from the newer output are returned
        assert retrieved == second_output.detections

    def test_filters_by_before_datetime(
        self,
        db_connection: sqlite3.Connection,
        deployment: data.Deployment,
    ) -> None:
        base_time = datetime.datetime.now(datetime.timezone.utc)
        first_recording = build_recording(
            deployment,
            path="first.wav",
            created_on=base_time,
        )
        second_recording = build_recording(
            deployment,
            path="second.wav",
            created_on=base_time + datetime.timedelta(seconds=10),
        )
        first_output = build_model_output(
            first_recording,
            name_model="test_model",
            created_on=base_time,
            file_tag=("test", "value1", 0.8),
            detection_score=0.6,
            detection_tag=("test2", "value3", 0.3),
        )
        second_output = build_model_output(
            second_recording,
            name_model="other_model",
            created_on=base_time + datetime.timedelta(seconds=10),
            file_tag=("site", "second", 0.5),
            detection_score=0.2,
            detection_tag=("species", "other", 0.1),
        )

        queries.create_deployment(db_connection, deployment)
        queries.create_recording(db_connection, first_recording, deployment)
        queries.insert_model_outputs(db_connection, [first_output])
        queries.create_recording(db_connection, second_recording, deployment)
        queries.insert_model_outputs(db_connection, [second_output])

        # When filtering detections before the older output time
        retrieved = queries.get_detections(
            db_connection,
            before=first_output.created_on,
        )

        # Then only detections from the older output are returned
        assert retrieved == first_output.detections


class TestGetPredictedTags:
    def test_filters_by_detection_id(
        self,
        db_connection: sqlite3.Connection,
        deployment: data.Deployment,
        recording: data.Recording,
        model_output: data.ModelOutput,
    ) -> None:
        detection = model_output.detections[0]

        # Given a seeded database connection
        queries.create_deployment(db_connection, deployment)
        queries.create_recording(db_connection, recording, deployment)
        queries.insert_model_outputs(db_connection, [model_output])

        # When filtering predicted tags by detection id
        retrieved = queries.get_predicted_tags(
            db_connection,
            detection_ids=[detection.id],
        )

        # Then only the tags for that detection are returned
        assert retrieved == detection.tags

    def test_filters_by_after_datetime(
        self,
        db_connection: sqlite3.Connection,
        deployment: data.Deployment,
    ) -> None:
        base_time = datetime.datetime.now(datetime.timezone.utc)
        first_recording = build_recording(
            deployment,
            path="first.wav",
            created_on=base_time,
        )
        second_recording = build_recording(
            deployment,
            path="second.wav",
            created_on=base_time + datetime.timedelta(seconds=10),
        )
        first_output = build_model_output(
            first_recording,
            name_model="test_model",
            created_on=base_time,
            file_tag=("test", "value1", 0.8),
            detection_score=0.6,
            detection_tag=("test2", "value3", 0.3),
        )
        second_output = build_model_output(
            second_recording,
            name_model="other_model",
            created_on=base_time + datetime.timedelta(seconds=10),
            file_tag=("site", "second", 0.5),
            detection_score=0.2,
            detection_tag=("species", "other", 0.1),
        )

        queries.create_deployment(db_connection, deployment)
        queries.create_recording(db_connection, first_recording, deployment)
        queries.insert_model_outputs(db_connection, [first_output])
        queries.create_recording(db_connection, second_recording, deployment)
        queries.insert_model_outputs(db_connection, [second_output])

        # When filtering predicted tags after the newer output time
        retrieved = queries.get_predicted_tags(
            db_connection,
            after=second_output.created_on,
        )

        # Then only tags associated with the newer detection output are returned
        assert retrieved == second_output.detections[0].tags

    def test_filters_by_before_datetime(
        self,
        db_connection: sqlite3.Connection,
        deployment: data.Deployment,
    ) -> None:
        base_time = datetime.datetime.now(datetime.timezone.utc)
        first_recording = build_recording(
            deployment,
            path="first.wav",
            created_on=base_time,
        )
        second_recording = build_recording(
            deployment,
            path="second.wav",
            created_on=base_time + datetime.timedelta(seconds=10),
        )
        first_output = build_model_output(
            first_recording,
            name_model="test_model",
            created_on=base_time,
            file_tag=("test", "value1", 0.8),
            detection_score=0.6,
            detection_tag=("test2", "value3", 0.3),
        )
        second_output = build_model_output(
            second_recording,
            name_model="other_model",
            created_on=base_time + datetime.timedelta(seconds=10),
            file_tag=("site", "second", 0.5),
            detection_score=0.2,
            detection_tag=("species", "other", 0.1),
        )

        queries.create_deployment(db_connection, deployment)
        queries.create_recording(db_connection, first_recording, deployment)
        queries.insert_model_outputs(db_connection, [first_output])
        queries.create_recording(db_connection, second_recording, deployment)
        queries.insert_model_outputs(db_connection, [second_output])

        # When filtering predicted tags before the older output time
        retrieved = queries.get_predicted_tags(
            db_connection,
            before=first_output.created_on,
        )

        # Then only tags associated with the older detection output are returned
        assert retrieved == first_output.detections[0].tags

    def test_filters_by_score_gt(
        self,
        db_connection: sqlite3.Connection,
        deployment: data.Deployment,
    ) -> None:
        base_time = datetime.datetime.now(datetime.timezone.utc)
        first_recording = build_recording(
            deployment,
            path="first.wav",
            created_on=base_time,
        )
        second_recording = build_recording(
            deployment,
            path="second.wav",
            created_on=base_time + datetime.timedelta(seconds=10),
        )
        first_output = build_model_output(
            first_recording,
            name_model="test_model",
            created_on=base_time,
            file_tag=("test", "value1", 0.8),
            detection_score=0.6,
            detection_tag=("test2", "value3", 0.3),
        )
        second_output = build_model_output(
            second_recording,
            name_model="other_model",
            created_on=base_time + datetime.timedelta(seconds=10),
            file_tag=("site", "second", 0.5),
            detection_score=0.2,
            detection_tag=("species", "other", 0.1),
        )

        queries.create_deployment(db_connection, deployment)
        queries.create_recording(db_connection, first_recording, deployment)
        queries.insert_model_outputs(db_connection, [first_output])
        queries.create_recording(db_connection, second_recording, deployment)
        queries.insert_model_outputs(db_connection, [second_output])

        # When filtering predicted tags above a confidence threshold
        retrieved = queries.get_predicted_tags(db_connection, score_gt=0.25)

        # Then only tags above the threshold are returned
        assert retrieved == [
            first_output.tags[0],
            first_output.detections[0].tags[0],
            second_output.tags[0],
        ]

    def test_filters_by_score_lt(
        self,
        db_connection: sqlite3.Connection,
        deployment: data.Deployment,
    ) -> None:
        base_time = datetime.datetime.now(datetime.timezone.utc)
        first_recording = build_recording(
            deployment,
            path="first.wav",
            created_on=base_time,
        )
        second_recording = build_recording(
            deployment,
            path="second.wav",
            created_on=base_time + datetime.timedelta(seconds=10),
        )
        first_output = build_model_output(
            first_recording,
            name_model="test_model",
            created_on=base_time,
            file_tag=("test", "value1", 0.8),
            detection_score=0.6,
            detection_tag=("test2", "value3", 0.3),
        )
        second_output = build_model_output(
            second_recording,
            name_model="other_model",
            created_on=base_time + datetime.timedelta(seconds=10),
            file_tag=("site", "second", 0.5),
            detection_score=0.2,
            detection_tag=("species", "other", 0.1),
        )

        queries.create_deployment(db_connection, deployment)
        queries.create_recording(db_connection, first_recording, deployment)
        queries.insert_model_outputs(db_connection, [first_output])
        queries.create_recording(db_connection, second_recording, deployment)
        queries.insert_model_outputs(db_connection, [second_output])

        # When filtering predicted tags below a confidence threshold
        retrieved = queries.get_predicted_tags(db_connection, score_lt=0.25)

        # Then only the low-confidence detection tags are returned
        assert retrieved == [second_output.detections[0].tags[0]]

    def test_filters_by_key(
        self,
        db_connection: sqlite3.Connection,
        deployment: data.Deployment,
    ) -> None:
        base_time = datetime.datetime.now(datetime.timezone.utc)
        first_recording = build_recording(
            deployment,
            path="first.wav",
            created_on=base_time,
        )
        second_recording = build_recording(
            deployment,
            path="second.wav",
            created_on=base_time + datetime.timedelta(seconds=10),
        )
        first_output = build_model_output(
            first_recording,
            name_model="test_model",
            created_on=base_time,
            file_tag=("test", "value1", 0.8),
            detection_score=0.6,
            detection_tag=("test2", "value3", 0.3),
        )
        second_output = build_model_output(
            second_recording,
            name_model="other_model",
            created_on=base_time + datetime.timedelta(seconds=10),
            file_tag=("site", "second", 0.5),
            detection_score=0.2,
            detection_tag=("species", "other", 0.1),
        )

        queries.create_deployment(db_connection, deployment)
        queries.create_recording(db_connection, first_recording, deployment)
        queries.insert_model_outputs(db_connection, [first_output])
        queries.create_recording(db_connection, second_recording, deployment)
        queries.insert_model_outputs(db_connection, [second_output])

        # When filtering predicted tags by key
        retrieved = queries.get_predicted_tags(db_connection, keys=["species"])

        # Then only tags with that key are returned
        assert retrieved == second_output.detections[0].tags

    def test_filters_by_value(
        self,
        db_connection: sqlite3.Connection,
        deployment: data.Deployment,
    ) -> None:
        base_time = datetime.datetime.now(datetime.timezone.utc)
        first_recording = build_recording(
            deployment,
            path="first.wav",
            created_on=base_time,
        )
        second_recording = build_recording(
            deployment,
            path="second.wav",
            created_on=base_time + datetime.timedelta(seconds=10),
        )
        first_output = build_model_output(
            first_recording,
            name_model="test_model",
            created_on=base_time,
            file_tag=("test", "value1", 0.8),
            detection_score=0.6,
            detection_tag=("test2", "value3", 0.3),
        )
        second_output = build_model_output(
            second_recording,
            name_model="other_model",
            created_on=base_time + datetime.timedelta(seconds=10),
            file_tag=("site", "second", 0.5),
            detection_score=0.2,
            detection_tag=("species", "other", 0.1),
        )

        queries.create_deployment(db_connection, deployment)
        queries.create_recording(db_connection, first_recording, deployment)
        queries.insert_model_outputs(db_connection, [first_output])
        queries.create_recording(db_connection, second_recording, deployment)
        queries.insert_model_outputs(db_connection, [second_output])

        # When filtering predicted tags by value
        retrieved = queries.get_predicted_tags(
            db_connection, values=["value3"]
        )

        # Then only tags with that value are returned
        assert retrieved == [first_output.detections[0].tags[0]]


class TestUpdateRecordingPath:
    def test_persists_new_path(
        self,
        db_connection: sqlite3.Connection,
        deployment: data.Deployment,
        recording: data.Recording,
    ) -> None:
        new_path = Path("updated.wav")

        # Given a stored recording
        queries.create_deployment(db_connection, deployment)
        queries.create_recording(db_connection, recording, deployment)

        # When updating the stored path
        queries.update_recording_path(db_connection, recording.id, new_path)

        # Then the persisted recording reflects the new path
        retrieved = queries.get_recordings_by_ids(
            db_connection, [recording.id]
        )
        assert retrieved == [recording.model_copy(update=dict(path=new_path))]
