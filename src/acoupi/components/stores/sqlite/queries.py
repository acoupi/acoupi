"""SQLite metadata-store query helpers."""

import datetime
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from acoupi import data

SQLITE_MAX_BOUND_VARIABLES = 900


def get_current_deployment(
    connection: sqlite3.Connection,
) -> Optional[data.Deployment]:
    row = connection.execute(
        """
        SELECT id, name, latitude, longitude, started_on, ended_on
        FROM deployment
        ORDER BY started_on DESC
        LIMIT 1
        """
    ).fetchone()
    if row is None:
        return None
    return row_to_deployment(row)


def create_deployment(
    connection: sqlite3.Connection,
    deployment: data.Deployment,
) -> data.Deployment:
    connection.execute(
        """
        INSERT INTO deployment (
            id, started_on, name, latitude, longitude, ended_on
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            deployment.id.bytes,
            serialise_datetime(deployment.started_on),
            deployment.name,
            deployment.latitude,
            deployment.longitude,
            None
            if deployment.ended_on is None
            else serialise_datetime(deployment.ended_on),
        ),
    )
    return deployment


def update_deployment(
    connection: sqlite3.Connection,
    deployment: data.Deployment,
) -> None:
    cursor = connection.execute(
        """
        UPDATE deployment
        SET name = ?, latitude = ?, longitude = ?, ended_on = ?
        WHERE id = ?
        """,
        (
            deployment.name,
            deployment.latitude,
            deployment.longitude,
            None
            if deployment.ended_on is None
            else serialise_datetime(deployment.ended_on),
            deployment.id.bytes,
        ),
    )
    if cursor.rowcount == 0:
        raise ValueError("No deployment found")


def get_deployment_by_id(
    connection: sqlite3.Connection,
    id: UUID,
) -> data.Deployment:
    row = connection.execute(
        """
        SELECT id, name, latitude, longitude, started_on, ended_on
        FROM deployment
        WHERE id = ?
        """,
        (id.bytes,),
    ).fetchone()
    if row is None:
        raise ValueError("No deployment found")
    return row_to_deployment(row)


def create_recording(
    connection: sqlite3.Connection,
    recording: data.Recording,
    deployment: data.Deployment,
) -> data.Recording:
    connection.execute(
        """
        INSERT INTO recording (
            id, path, duration_s, samplerate_hz,
            audio_channels, datetime, deployment_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            recording.id.bytes,
            None if recording.path is None else str(recording.path),
            recording.duration,
            recording.samplerate,
            recording.audio_channels,
            serialise_datetime(recording.created_on),
            deployment.id.bytes,
        ),
    )
    return recording


def get_existing_recording_ids(
    connection: sqlite3.Connection,
    recording_ids: List[UUID],
) -> set[UUID]:
    if not recording_ids:
        return set()

    rows = []
    for recording_id_chunk in chunked_uuids(recording_ids):
        placeholders = ", ".join("?" for _ in recording_id_chunk)
        query = f"SELECT id FROM recording WHERE id IN ({placeholders})"
        rows.extend(
            connection.execute(
                query,
                [recording_id.bytes for recording_id in recording_id_chunk],
            ).fetchall()
        )

    return {UUID(bytes=row[0]) for row in rows}


def get_recordings_by_paths(
    connection: sqlite3.Connection,
    paths: List[str],
) -> List[data.Recording]:
    placeholders = ", ".join("?" for _ in paths)
    rows = connection.execute(
        f"""
        SELECT r.id, r.path, r.duration_s, r.samplerate_hz,
               r.audio_channels, r.datetime, d.id AS deployment_id,
               d.name AS deployment_name, d.latitude, d.longitude,
               d.started_on, d.ended_on
        FROM recording AS r
        JOIN deployment AS d ON d.id = r.deployment_id
        WHERE r.path IN ({placeholders})
        ORDER BY r.datetime DESC
        """,
        paths,
    ).fetchall()
    return [row_to_recording(row) for row in rows]


def get_recordings_by_ids(
    connection: sqlite3.Connection,
    ids: List[UUID],
) -> List[data.Recording]:
    if not ids:
        return []

    rows = []
    for id_chunk in chunked_uuids(ids):
        placeholders = ", ".join("?" for _ in id_chunk)
        rows.extend(
            connection.execute(
                f"""
                SELECT r.id, r.path, r.duration_s, r.samplerate_hz,
                       r.audio_channels, r.datetime, d.id AS deployment_id,
                       d.name AS deployment_name, d.latitude, d.longitude,
                       d.started_on, d.ended_on
                FROM recording AS r
                JOIN deployment AS d ON d.id = r.deployment_id
                WHERE r.id IN ({placeholders})
                ORDER BY r.datetime DESC
                """,
                [recording_id.bytes for recording_id in id_chunk],
            ).fetchall()
        )
    return [row_to_recording(row) for row in rows]


def get_recordings_model_output_info(
    connection: sqlite3.Connection,
    recording_ids: List[UUID],
) -> Dict[UUID, List[data.ModelOutputInfo]]:
    outputs_by_recording_id: Dict[UUID, List[data.ModelOutputInfo]] = (
        defaultdict(list)
    )
    for recording_id_chunk in chunked_uuids(recording_ids):
        placeholders = ", ".join("?" for _ in recording_id_chunk)
        rows = connection.execute(
            "SELECT id, model_name, recording_id, created_on "
            f"FROM model_output WHERE recording_id IN ({placeholders})",
            [recording_id.bytes for recording_id in recording_id_chunk],
        ).fetchall()
        for row in rows:
            outputs_by_recording_id[UUID(bytes=row["recording_id"])].append(
                data.ModelOutputInfo(
                    id=UUID(bytes=row["id"]),
                    name_model=row["model_name"],
                    created_on=parse_datetime(row["created_on"]),
                )
            )
    return dict(outputs_by_recording_id)


def get_recordings_model_outputs(
    connection: sqlite3.Connection,
    recordings_by_id: Dict[UUID, data.Recording],
) -> Dict[UUID, List[data.ModelOutput]]:
    recording_ids = list(recordings_by_id)
    model_output_rows: Dict[
        UUID, List[Tuple[UUID, str, data.AwareDatetime]]
    ] = defaultdict(list)

    for recording_id_chunk in chunked_uuids(recording_ids):
        placeholders = ", ".join("?" for _ in recording_id_chunk)
        rows = connection.execute(
            "SELECT id, recording_id, model_name, created_on "
            f"FROM model_output WHERE recording_id IN ({placeholders})",
            [recording_id.bytes for recording_id in recording_id_chunk],
        ).fetchall()

        for (
            model_output_id_blob,
            recording_id_blob,
            model_name,
            created_on,
        ) in rows:
            model_output_rows[UUID(bytes=recording_id_blob)].append(
                (
                    UUID(bytes=model_output_id_blob),
                    model_name,
                    parse_datetime(created_on),
                )
            )

    if not model_output_rows:
        return {}

    model_output_ids = [
        model_output_id
        for rows in model_output_rows.values()
        for model_output_id, _, _ in rows
    ]
    detections_by_model_output_id = get_detections_by_model_output_ids(
        connection,
        model_output_ids,
    )
    outputs_by_recording_id: Dict[UUID, List[data.ModelOutput]] = {}
    for recording_id, rows in model_output_rows.items():
        recording = recordings_by_id[recording_id]
        outputs_by_recording_id[recording_id] = [
            data.ModelOutput(
                id=model_output_id,
                name_model=model_name,
                recording=recording,
                created_on=created_on,
                detections=detections_by_model_output_id.get(
                    model_output_id, []
                ),
            )
            for model_output_id, model_name, created_on in rows
        ]

    return outputs_by_recording_id


def get_model_outputs(
    connection: sqlite3.Connection,
    after: Optional[data.AwareDatetime] = None,
    before: Optional[data.AwareDatetime] = None,
    ids: Optional[List[UUID]] = None,
    recording_ids: Optional[List[UUID]] = None,
    model_names: Optional[List[str]] = None,
    detection_ids: Optional[List[UUID]] = None,
    limit: Optional[int] = None,
) -> List[data.ModelOutput]:
    query = [
        """
        SELECT mo.id, mo.model_name, mo.recording_id, mo.created_on
        FROM model_output AS mo
        """
    ]
    clauses = []
    params: List[object] = []

    if detection_ids:
        placeholders = ", ".join("?" for _ in detection_ids)
        clauses.append(
            "EXISTS (SELECT 1 FROM detection AS d "
            f"WHERE d.model_output_id = mo.id AND d.id IN ({placeholders}))"
        )
        params.extend(detection_id.bytes for detection_id in detection_ids)

    if after is not None:
        clauses.append("mo.created_on >= ?")
        params.append(serialise_datetime(after))

    if before is not None:
        clauses.append("mo.created_on <= ?")
        params.append(serialise_datetime(before))

    if ids is not None:
        placeholders = ", ".join("?" for _ in ids)
        clauses.append(f"mo.id IN ({placeholders})")
        params.extend(model_output_id.bytes for model_output_id in ids)

    if recording_ids is not None:
        placeholders = ", ".join("?" for _ in recording_ids)
        clauses.append(f"mo.recording_id IN ({placeholders})")
        params.extend(recording_id.bytes for recording_id in recording_ids)

    if model_names is not None:
        placeholders = ", ".join("?" for _ in model_names)
        clauses.append(f"mo.model_name IN ({placeholders})")
        params.extend(model_names)

    if clauses:
        query.append("WHERE " + " AND ".join(clauses))

    query.append("ORDER BY mo.created_on DESC")
    if limit is not None:
        query.append("LIMIT ?")
        params.append(limit)

    rows = connection.execute(" ".join(query), params).fetchall()
    if not rows:
        return []

    recording_ids_in_rows = list(
        {UUID(bytes=row["recording_id"]) for row in rows}
    )
    recordings = get_recordings_by_ids(connection, recording_ids_in_rows)
    recordings_by_id = {recording.id: recording for recording in recordings}
    outputs_by_recording_id = get_recordings_model_outputs(
        connection,
        recordings_by_id,
    )

    outputs: List[data.ModelOutput] = []
    for row in rows:
        recording_id = UUID(bytes=row["recording_id"])
        model_output_id = UUID(bytes=row["id"])
        outputs.extend(
            output
            for output in outputs_by_recording_id.get(recording_id, [])
            if output.id == model_output_id
        )
    return outputs


def get_detections(
    connection: sqlite3.Connection,
    ids: Optional[List[UUID]] = None,
    model_output_ids: Optional[List[UUID]] = None,
    score_gt: Optional[float] = None,
    score_lt: Optional[float] = None,
    model_names: Optional[List[str]] = None,
    after: Optional[data.AwareDatetime] = None,
    before: Optional[data.AwareDatetime] = None,
) -> List[data.Detection]:
    query = [
        """
        SELECT d.id, d.start_time_s, d.end_time_s, d.low_freq_hz,
               d.high_freq_hz, d.detection_score, d.model_output_id,
               d.prediction_type
        FROM detection AS d
        JOIN model_output AS mo ON mo.id = d.model_output_id
        """
    ]
    clauses = []
    params: List[object] = []

    if ids:
        placeholders = ", ".join("?" for _ in ids)
        clauses.append(f"d.id IN ({placeholders})")
        params.extend(detection_id.bytes for detection_id in ids)

    if model_output_ids:
        placeholders = ", ".join("?" for _ in model_output_ids)
        clauses.append(f"d.model_output_id IN ({placeholders})")
        params.extend(
            model_output_id.bytes for model_output_id in model_output_ids
        )

    if score_gt is not None:
        clauses.append("d.detection_score > ?")
        params.append(score_gt)

    if score_lt is not None:
        clauses.append("d.detection_score < ?")
        params.append(score_lt)

    if after is not None:
        clauses.append("mo.created_on >= ?")
        params.append(serialise_datetime(after))

    if before is not None:
        clauses.append("mo.created_on <= ?")
        params.append(serialise_datetime(before))

    if model_names:
        placeholders = ", ".join("?" for _ in model_names)
        clauses.append(f"mo.model_name IN ({placeholders})")
        params.extend(model_names)

    if clauses:
        query.append("WHERE " + " AND ".join(clauses))

    rows = connection.execute(" ".join(query), params).fetchall()
    detection_ids = [UUID(bytes=row["id"]) for row in rows]
    tags_by_detection_id = get_predicted_tags_by_parent_ids(
        connection,
        detection_ids,
        column_name="detection_id",
    )

    return [
        data.Detection(
            id=UUID(bytes=row["id"]),
            prediction_type=data.PredictionType(row["prediction_type"]),
            location=None
            if (
                row["start_time_s"] is None
                or row["end_time_s"] is None
                or row["low_freq_hz"] is None
                or row["high_freq_hz"] is None
            )
            else data.BoundingBox(
                coordinates=(
                    row["start_time_s"],
                    row["low_freq_hz"],
                    row["end_time_s"],
                    row["high_freq_hz"],
                )
            ),
            detection_score=row["detection_score"],
            tags=tags_by_detection_id.get(row["id"], []),
        )
        for row in rows
    ]


def get_predicted_tags(
    connection: sqlite3.Connection,
    detection_ids: Optional[List[UUID]] = None,
    after: Optional[data.AwareDatetime] = None,
    before: Optional[data.AwareDatetime] = None,
    score_gt: Optional[float] = None,
    score_lt: Optional[float] = None,
    keys: Optional[List[str]] = None,
    values: Optional[List[str]] = None,
) -> List[data.PredictedTag]:
    query = [
        """
        SELECT pt.key, pt.value, pt.confidence_score
        FROM predicted_tag AS pt
        LEFT JOIN detection AS d ON d.id = pt.detection_id
        LEFT JOIN model_output AS mo ON mo.id = d.model_output_id
        """
    ]
    clauses = []
    params: List[object] = []

    if detection_ids:
        placeholders = ", ".join("?" for _ in detection_ids)
        clauses.append(f"pt.detection_id IN ({placeholders})")
        params.extend(detection_id.bytes for detection_id in detection_ids)

    if after is not None:
        clauses.append("mo.created_on >= ?")
        params.append(serialise_datetime(after))

    if before is not None:
        clauses.append("mo.created_on <= ?")
        params.append(serialise_datetime(before))

    if score_gt is not None:
        clauses.append("pt.confidence_score > ?")
        params.append(score_gt)

    if score_lt is not None:
        clauses.append("pt.confidence_score < ?")
        params.append(score_lt)

    if keys:
        placeholders = ", ".join("?" for _ in keys)
        clauses.append(f"pt.key IN ({placeholders})")
        params.extend(keys)

    if values:
        placeholders = ", ".join("?" for _ in values)
        clauses.append(f"pt.value IN ({placeholders})")
        params.extend(values)

    if clauses:
        query.append("WHERE " + " AND ".join(clauses))

    rows = connection.execute(" ".join(query), params).fetchall()
    return [row_to_predicted_tag(row) for row in rows]


def update_recording_path(
    connection: sqlite3.Connection,
    recording_id: UUID,
    path: Path,
) -> None:
    connection.execute(
        "UPDATE recording SET path = ? WHERE id = ?",
        (str(path), recording_id.bytes),
    )


def insert_model_outputs(
    connection: sqlite3.Connection,
    model_outputs: List[data.ModelOutput],
) -> None:
    model_output_rows = []
    predicted_tag_rows = []
    detection_rows = []

    for model_output in model_outputs:
        model_output_rows.append(
            (
                model_output.id.bytes,
                model_output.name_model,
                model_output.recording.id.bytes,
                serialise_datetime(model_output.created_on),
            )
        )

        for detection in model_output.detections:
            bbox = detection.location
            detection_rows.append(
                (
                    detection.id.bytes,
                    detection.prediction_type.value,
                    None if bbox is None else bbox.coordinates[0],
                    None if bbox is None else bbox.coordinates[2],
                    None if bbox is None else bbox.coordinates[1],
                    None if bbox is None else bbox.coordinates[3],
                    detection.detection_score,
                    model_output.id.bytes,
                )
            )

            for tag in detection.tags:
                predicted_tag_rows.append(
                    (
                        tag.tag.key,
                        tag.tag.value,
                        tag.confidence_score,
                        detection.id.bytes,
                    )
                )

    connection.executemany(
        "INSERT INTO model_output (id, model_name, recording_id, created_on) VALUES (?, ?, ?, ?)",
        model_output_rows,
    )
    if detection_rows:
        connection.executemany(
            "INSERT INTO detection (id, prediction_type, start_time_s, end_time_s, low_freq_hz, high_freq_hz, detection_score, model_output_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            detection_rows,
        )
    if predicted_tag_rows:
        connection.executemany(
            "INSERT INTO predicted_tag (key, value, confidence_score, detection_id) VALUES (?, ?, ?, ?)",
            predicted_tag_rows,
        )


def get_detections_by_model_output_ids(
    connection: sqlite3.Connection,
    model_output_ids: List[UUID],
) -> Dict[UUID, List[data.Detection]]:
    if not model_output_ids:
        return {}

    detection_rows = []
    for model_output_id_chunk in chunked_uuids(model_output_ids):
        placeholders = ", ".join("?" for _ in model_output_id_chunk)
        detection_rows.extend(
            connection.execute(
                "SELECT id, prediction_type, start_time_s, end_time_s, low_freq_hz, high_freq_hz, detection_score, model_output_id "
                f"FROM detection WHERE model_output_id IN ({placeholders})",
                [
                    model_output_id.bytes
                    for model_output_id in model_output_id_chunk
                ],
            ).fetchall()
        )

    detection_ids = [UUID(bytes=row[0]) for row in detection_rows]
    tags_by_detection_id = get_predicted_tags_by_parent_ids(
        connection,
        detection_ids,
        column_name="detection_id",
    )

    detections_by_model_output_id: Dict[UUID, List[data.Detection]] = (
        defaultdict(list)
    )
    for (
        detection_id_blob,
        prediction_type,
        start_time_s,
        end_time_s,
        low_freq_hz,
        high_freq_hz,
        detection_score,
        model_output_id_blob,
    ) in detection_rows:
        if (
            start_time_s is None
            or end_time_s is None
            or low_freq_hz is None
            or high_freq_hz is None
        ):
            location = None
        else:
            location = data.BoundingBox(
                coordinates=(
                    start_time_s,
                    low_freq_hz,
                    end_time_s,
                    high_freq_hz,
                )
            )

        model_output_id = UUID(bytes=model_output_id_blob)
        detections_by_model_output_id[model_output_id].append(
            data.Detection(
                id=UUID(bytes=detection_id_blob),
                prediction_type=data.PredictionType(prediction_type),
                location=location,
                detection_score=detection_score,
                tags=tags_by_detection_id.get(detection_id_blob, []),
            )
        )

    return dict(detections_by_model_output_id)


def get_predicted_tags_by_parent_ids(
    connection: sqlite3.Connection,
    ids: List[UUID],
    column_name: str,
) -> Dict[bytes, List[data.PredictedTag]]:
    tags_by_id: Dict[bytes, List[data.PredictedTag]] = defaultdict(list)
    for id_chunk in chunked_uuids(ids):
        placeholders = ", ".join("?" for _ in id_chunk)
        rows = connection.execute(
            "SELECT key, value, confidence_score, "
            f"{column_name} FROM predicted_tag WHERE {column_name} IN ({placeholders}) ORDER BY rowid",
            [id_value.bytes for id_value in id_chunk],
        ).fetchall()

        for key, value, confidence_score, id_blob in rows:
            tags_by_id[id_blob].append(
                data.PredictedTag(
                    tag=data.Tag(key=key, value=value),
                    confidence_score=confidence_score,
                )
            )

    return dict(tags_by_id)


def row_to_deployment(row: sqlite3.Row) -> data.Deployment:
    return data.Deployment(
        id=UUID(bytes=row["id"]),
        name=row["name"],
        latitude=row["latitude"],
        longitude=row["longitude"],
        started_on=parse_datetime(row["started_on"]),
        ended_on=None
        if row["ended_on"] is None
        else parse_datetime(row["ended_on"]),
    )


def row_to_recording(row: sqlite3.Row) -> data.Recording:
    return data.Recording(
        id=UUID(bytes=row["id"]),
        deployment=data.Deployment(
            id=UUID(bytes=row["deployment_id"]),
            name=row["deployment_name"],
            latitude=row["latitude"],
            longitude=row["longitude"],
            started_on=parse_datetime(row["started_on"]),
            ended_on=None
            if row["ended_on"] is None
            else parse_datetime(row["ended_on"]),
        ),
        created_on=parse_datetime(row["datetime"]),
        duration=row["duration_s"],
        samplerate=row["samplerate_hz"],
        audio_channels=row["audio_channels"],
        path=None if row["path"] is None else Path(row["path"]),
    )


def row_to_predicted_tag(row: sqlite3.Row) -> data.PredictedTag:
    return data.PredictedTag(
        tag=data.Tag(key=row["key"], value=row["value"]),
        confidence_score=row["confidence_score"],
    )


def chunked_uuids(ids: List[UUID]) -> List[List[UUID]]:
    return [
        ids[index : index + SQLITE_MAX_BOUND_VARIABLES]
        for index in range(0, len(ids), SQLITE_MAX_BOUND_VARIABLES)
    ]


def serialise_datetime(value: data.AwareDatetime) -> str:
    return value.isoformat()


def parse_datetime(value: str) -> data.AwareDatetime:
    parsed = datetime.datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=datetime.timezone.utc)
    return parsed
