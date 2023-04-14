"""Test the SQLite Message store."""
import datetime
import sqlite3
from pathlib import Path
from typing import Generator, List, Optional
from uuid import UUID

import pytest

from acoupi import types
from acoupi.storages.sqlite.message_store import SqliteMessageStore


class _DummyStore(types.Store):
    def get_current_deployment(self) -> types.Deployment:
        return types.Deployment(
            device_id="device_id",
            started_on=datetime.datetime.now(),
            name="name",
            latitude=1.0,
            longitude=1.0,
        )

    def store_recording(
        self,
        recording: types.Recording,
        deployment: Optional[types.Deployment] = None,
    ) -> None:
        pass

    def store_deployment(self, deployment: types.Deployment) -> None:
        pass

    def store_detections(
        self,
        recording: types.Recording,
        detections: List[types.Detection],
    ) -> None:
        pass

    def get_recordings(
        self,
        include: Optional[List[UUID]] = None,
        exclude: Optional[List[UUID]] = None,
    ) -> List[types.Recording]:
        return []

    def get_detections(
        self,
        include: Optional[List[UUID]] = None,
        exclude: Optional[List[UUID]] = None,
    ) -> List[types.Detection]:
        return []

    def get_deployments(
        self,
        include: Optional[List[UUID]] = None,
        exclude: Optional[List[UUID]] = None,
    ) -> List[types.Deployment]:
        return []


@pytest.fixture(scope="function")
def sqlite_message_store(
    tmp_path: Path,
) -> Generator[SqliteMessageStore, None, None]:
    """Create a store."""
    message_db_path = tmp_path / "message_test.db"
    store = _DummyStore()
    message_store = SqliteMessageStore(str(message_db_path), store)
    yield message_store
    message_db_path.unlink()


def test_message_status_table_has_correct_columns(
    sqlite_message_store,
) -> None:
    """Test that the message_status table has the correct columns."""
    expected_columns = {
        "id",
        "response_ok",
        "response_code",
        "sent_on",
    }
    db_path = sqlite_message_store.db_path

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(message_status);")
        actual_columns = set(row[1] for row in cursor.fetchall())
        assert expected_columns == actual_columns


def test_deployment_message_table_has_correct_columns(
    sqlite_message_store,
) -> None:
    """Test that the deployment_message table has the correct columns."""
    expected_columns = {"id", "deployment_id", "message_status_id"}
    db_path = sqlite_message_store.db_path

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(deployment_message);")
        actual_columns = set(row[1] for row in cursor.fetchall())
        assert expected_columns == actual_columns


def test_recording_message_table_has_correct_columns(
    sqlite_message_store,
) -> None:
    """Test that the recording_message table has the correct columns."""
    expected_columns = {"id", "recording_id", "message_status_id"}
    db_path = sqlite_message_store.db_path

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(recording_message);")
        actual_columns = set(row[1] for row in cursor.fetchall())
        assert expected_columns == actual_columns


def test_detection_message_table_has_correct_columns(
    sqlite_message_store,
) -> None:
    """Test that the detection_message table has the correct columns."""
    expected_columns = {"id", "detection_id", "message_status_id"}
    db_path = sqlite_message_store.db_path

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(detection_message);")
        actual_columns = set(row[1] for row in cursor.fetchall())
        assert expected_columns == actual_columns


def test_store_deployment_message(sqlite_message_store):
    """Test that a deployment message can be stored."""
    # Arrange
    deployment = types.Deployment(
        device_id="device_id",
        started_on=datetime.datetime.now(),
        name="name",
        latitude=1.0,
        longitude=1.0,
    )

    message = types.Message(
        sent_on=datetime.datetime.now(),
        device_id="device_id",
        message="message",
    )

    response = types.Response(
        received_on=datetime.datetime.now(),
        status=types.ResponseStatus.SUCCESS,
        message=message,
    )

    # Act
    sqlite_message_store.store_deployment_message(deployment, response)

    # Assert
    db_path = sqlite_message_store.db_path
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM deployment_message;")
        row = cursor.fetchone()
        assert row["deployment_id"] == deployment.id.bytes
        cursor.execute("SELECT * FROM message_status;")
        row = cursor.fetchone()
        assert row["response_ok"] == 1
        assert row["response_code"] == types.ResponseStatus.SUCCESS.value
        assert row["sent_on"] == message.sent_on.isoformat(sep=" ")


def test_store_recording_message(sqlite_message_store):
    """Test that a recording message can be stored."""
    # Arrange
    recording = types.Recording(
        path="path",
        datetime=datetime.datetime.now(),
        duration=1.0,
        samplerate=8000,
    )

    message = types.Message(
        sent_on=datetime.datetime.now(),
        device_id="device_id",
        message="message",
    )

    response = types.Response(
        received_on=datetime.datetime.now(),
        status=types.ResponseStatus.SUCCESS,
        message=message,
    )

    # Act
    sqlite_message_store.store_recording_message(recording, response)

    # Assert
    db_path = sqlite_message_store.db_path
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM recording_message;")
        row = cursor.fetchone()
        assert row["recording_id"] == recording.id.bytes
        cursor.execute("SELECT * FROM message_status;")
        row = cursor.fetchone()
        assert row["response_ok"] == 1
        assert row["response_code"] == types.ResponseStatus.SUCCESS.value
        assert row["sent_on"] == message.sent_on.isoformat(sep=" ")


def test_store_detection_message(sqlite_message_store):
    """Test that a detection message can be stored."""
    # Arrange
    detection = types.Detection(
        species_name="species_name",
        probability=1.0,
    )

    message = types.Message(
        sent_on=datetime.datetime.now(),
        device_id="device_id",
        message="message",
    )

    response = types.Response(
        received_on=datetime.datetime.now(),
        status=types.ResponseStatus.SUCCESS,
        message=message,
    )

    # Act
    sqlite_message_store.store_detection_message(detection, response)

    # Assert
    db_path = sqlite_message_store.db_path
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM detection_message;")
        row = cursor.fetchone()
        assert row["detection_id"] == detection.id.bytes
        cursor.execute("SELECT * FROM message_status;")
        row = cursor.fetchone()
        assert row["response_ok"] == 1
        assert row["response_code"] == types.ResponseStatus.SUCCESS.value
        assert row["sent_on"] == message.sent_on.isoformat(sep=" ")


def test_get_unsynced_deployments(
    sqlite_message_store: SqliteMessageStore,
    monkeypatch,
):
    """Test that unsynced deployments can be retrieved."""
    # Arrange
    deployment1 = types.Deployment(
        device_id="device_id",
        started_on=datetime.datetime.now(),
        name="name",
        latitude=1.0,
        longitude=1.0,
    )

    deployment2 = types.Deployment(
        device_id="device_id",
        started_on=datetime.datetime.now() + datetime.timedelta(days=1),
        name="different_name",
        latitude=1.0,
        longitude=1.0,
    )

    # Mock the get_deployments method to return the deployments we want
    def get_deployments(
        include: Optional[List[UUID]] = None,
        exclude: Optional[List[UUID]] = None,
    ) -> List[types.Deployment]:
        if include is not None and exclude is not None:
            raise ValueError("include and exclude cannot both be set")

        if include is not None:
            return [
                deployment
                for deployment in [deployment1, deployment2]
                if deployment.id in include
            ]

        if exclude is not None:
            return [
                deployment
                for deployment in [deployment1, deployment2]
                if deployment.id not in exclude
            ]

        return [deployment1, deployment2]

    monkeypatch.setattr(
        sqlite_message_store.store,
        "get_deployments",
        get_deployments,
    )

    # Act
    unsynced_deployments = sqlite_message_store.get_unsynced_deployments()

    # Assert
    assert len(unsynced_deployments) == 2
    assert unsynced_deployments[0] == deployment1
    assert unsynced_deployments[1] == deployment2

    # Arrage - Register the first deployment as synced
    message = types.Message(
        sent_on=datetime.datetime.now(),
        device_id="device_id",
        message="message",
    )

    response = types.Response(
        received_on=datetime.datetime.now(),
        status=types.ResponseStatus.SUCCESS,
        message=message,
    )

    sqlite_message_store.store_deployment_message(deployment1, response)

    # Act
    unsynced_deployments = sqlite_message_store.get_unsynced_deployments()

    # Assert
    assert len(unsynced_deployments) == 1
    assert unsynced_deployments[0] == deployment2


def test_get_unsynced_recordings(
    sqlite_message_store: SqliteMessageStore,
    monkeypatch,
):
    """Test that unsynced recordings can be retrieved."""
    # Arrange
    recording1 = types.Recording(
        path="path",
        datetime=datetime.datetime.now(),
        duration=1.0,
        samplerate=8000,
    )

    recording2 = types.Recording(
        path="path",
        datetime=datetime.datetime.now() + datetime.timedelta(days=1),
        duration=1.0,
        samplerate=8000,
    )

    # Mock the get_recordings method to return the recordings we want
    def get_recordings(
        include: Optional[List[UUID]] = None,
        exclude: Optional[List[UUID]] = None,
    ) -> List[types.Recording]:
        if include is not None and exclude is not None:
            raise ValueError("include and exclude cannot both be set")

        if include is not None:
            return [
                recording
                for recording in [recording1, recording2]
                if recording.id in include
            ]

        if exclude is not None:
            return [
                recording
                for recording in [recording1, recording2]
                if recording.id not in exclude
            ]

        return [recording1, recording2]

    monkeypatch.setattr(
        sqlite_message_store.store,
        "get_recordings",
        get_recordings,
    )

    # Act
    unsynced_recordings = sqlite_message_store.get_unsynced_recordings()

    # Assert
    assert len(unsynced_recordings) == 2
    assert unsynced_recordings[0] == recording1
    assert unsynced_recordings[1] == recording2

    # Arrage - Register the first recording as synced
    message = types.Message(
        sent_on=datetime.datetime.now(),
        device_id="device_id",
        message="message",
    )

    response = types.Response(
        received_on=datetime.datetime.now(),
        status=types.ResponseStatus.SUCCESS,
        message=message,
    )

    sqlite_message_store.store_recording_message(recording1, response)

    # Act
    unsynced_recordings = sqlite_message_store.get_unsynced_recordings()

    # Assert
    assert len(unsynced_recordings) == 1
    assert unsynced_recordings[0] == recording2


def test_get_unsynced_detections(
    sqlite_message_store: SqliteMessageStore,
    monkeypatch,
):
    """Test that unsynced detections can be retrieved."""
    # Arrange
    detection1 = types.Detection(
        species_name="species_name",
        probability=1.0,
    )

    detection2 = types.Detection(
        species_name="species_name_2",
        probability=0.8,
    )

    # Mock the get_detections method to return the detections we want
    def get_detections(
        include: Optional[List[UUID]] = None,
        exclude: Optional[List[UUID]] = None,
    ) -> List[types.Detection]:
        if include is not None and exclude is not None:
            raise ValueError("include and exclude cannot both be set")

        if include is not None:
            return [
                detection
                for detection in [detection1, detection2]
                if detection.id in include
            ]

        if exclude is not None:
            return [
                detection
                for detection in [detection1, detection2]
                if detection.id not in exclude
            ]

        return [detection1, detection2]

    monkeypatch.setattr(
        sqlite_message_store.store,
        "get_detections",
        get_detections,
    )

    # Act
    unsynced_detections = sqlite_message_store.get_unsynced_detections()

    # Assert
    assert len(unsynced_detections) == 2
    assert unsynced_detections[0] == detection1
    assert unsynced_detections[1] == detection2

    # Arrage - Register the first detection as synced
    message = types.Message(
        sent_on=datetime.datetime.now(),
        device_id="device_id",
        message="message",
    )

    response = types.Response(
        received_on=datetime.datetime.now(),
        status=types.ResponseStatus.SUCCESS,
        message=message,
    )

    sqlite_message_store.store_detection_message(detection1, response)

    # Act
    unsynced_detections = sqlite_message_store.get_unsynced_detections()

    # Assert
    assert len(unsynced_detections) == 1
    assert unsynced_detections[0] == detection2
