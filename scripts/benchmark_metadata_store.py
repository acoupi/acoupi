"""Benchmark the Acoupi metadata sqlite store.

This script creates a synthetic metadata database using the real
``acoupi.components.stores.SqliteStore`` implementation and measures common
write and read operations as the number of detections grows.

Examples
--------
Create a fresh database and benchmark moderate batches::

    uv run python scripts/benchmark_metadata_store.py \
        --db-path /tmp/acoupi-benchmark.db \
        --recordings 200 \
        --detections-per-output 100

Run a larger write benchmark and keep the generated database::

    uv run python scripts/benchmark_metadata_store.py \
        --db-path /tmp/acoupi-large.db \
        --recordings 1000 \
        --detections-per-output 500 \
        --keep-db
"""

from __future__ import annotations

import argparse
import datetime as dt
import sqlite3
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Sequence

from acoupi import data
from acoupi.components.stores import SqliteStore


@dataclass
class BenchmarkResult:
    """Single benchmark measurement."""

    name: str
    seconds: float
    extra: str = ""


@dataclass
class FlatRows:
    """Flattened benchmark rows for direct sqlite insertion."""

    deployment: tuple
    recordings: List[tuple]
    model_outputs: List[tuple]
    detections: List[tuple]
    predicted_tags: List[tuple]


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Create a synthetic Acoupi metadata database and benchmark "
            "write/read operations."
        )
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="Path to the sqlite database file to create/use.",
    )
    parser.add_argument(
        "--recordings",
        type=int,
        default=100,
        help="Number of recordings/model outputs to insert.",
    )
    parser.add_argument(
        "--detections-per-output",
        type=int,
        default=100,
        help="Number of detections to attach to each model output.",
    )
    parser.add_argument(
        "--tags-per-detection",
        type=int,
        default=1,
        help="Number of predicted tags to create for each detection.",
    )
    parser.add_argument(
        "--recording-tags",
        type=int,
        default=0,
        help="Number of recording-level tags to attach to each model output.",
    )
    parser.add_argument(
        "--read-limit",
        type=int,
        default=100,
        help="Limit used for the get_model_outputs benchmark.",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=100,
        help="Number of recording/model output/detection ids to sample for reads.",
    )
    parser.add_argument(
        "--keep-db",
        action="store_true",
        help="Keep any created database file after the benchmark finishes.",
    )
    parser.add_argument(
        "--reuse-db",
        action="store_true",
        help="Reuse an existing database file instead of deleting it first.",
    )
    parser.add_argument(
        "--compare-sqlite3",
        action="store_true",
        help="Also benchmark direct sqlite3 bulk insertion on the same payload.",
    )
    return parser


def make_tag(index: int, score: float) -> data.PredictedTag:
    """Create a deterministic predicted tag."""
    return data.PredictedTag(
        tag=data.Tag(key="species", value=f"species_{index % 10}"),
        confidence_score=score,
    )


def make_detection(index: int, tags_per_detection: int) -> data.Detection:
    """Create a deterministic synthetic detection."""
    tags = [
        make_tag(
            index=(index + tag_index), score=max(0.0, 0.99 - 0.01 * tag_index)
        )
        for tag_index in range(tags_per_detection)
    ]
    return data.Detection(
        location=data.BoundingBox.from_coordinates(
            start_time=float(index % 30) * 0.1,
            low_freq=1000.0 + float(index % 20) * 50.0,
            end_time=float(index % 30) * 0.1 + 0.5,
            high_freq=3000.0 + float(index % 20) * 50.0,
        ),
        detection_score=((index % 100) + 1) / 100,
        tags=tags,
    )


def make_model_output(
    deployment: data.Deployment,
    recording_index: int,
    detections_per_output: int,
    tags_per_detection: int,
    recording_tags: int,
    base_time: dt.datetime,
) -> data.ModelOutput:
    """Create one synthetic model output with its recording."""
    created_on = base_time + dt.timedelta(seconds=recording_index)
    recording = data.Recording(
        created_on=created_on,
        duration=3.0,
        samplerate=48_000,
        deployment=deployment,
        path=Path(f"/tmp/acoupi/recording_{recording_index:08d}.wav"),
        audio_channels=1,
    )
    detections = [
        make_detection(
            index=recording_index * detections_per_output + detection_index,
            tags_per_detection=tags_per_detection,
        )
        for detection_index in range(detections_per_output)
    ]
    tags = [
        make_tag(recording_index + tag_index, 0.95)
        for tag_index in range(recording_tags)
    ]
    return data.ModelOutput(
        name_model="benchmark-model",
        recording=recording,
        tags=tags,
        detections=detections,
        created_on=created_on,
    )


def time_call(
    name: str, func: Callable[[], object], extra: str = ""
) -> BenchmarkResult:
    """Measure one callable."""
    start = time.perf_counter()
    func()
    end = time.perf_counter()
    return BenchmarkResult(name=name, seconds=end - start, extra=extra)


def print_results(results: Sequence[BenchmarkResult]) -> None:
    """Print benchmark results as a compact table."""
    name_width = max(len(result.name) for result in results)
    for result in results:
        rate = ""
        if result.extra:
            rate = f" | {result.extra}"
        print(f"{result.name:<{name_width}} : {result.seconds:>9.4f} s{rate}")


def uuid_blob(value) -> bytes:
    """Convert a UUID to sqlite blob bytes."""
    return value.bytes


def prepare_sqlite_rows(
    deployment: data.Deployment,
    model_outputs: Sequence[data.ModelOutput],
) -> FlatRows:
    """Flatten benchmark payloads into sqlite-ready row tuples."""
    deployment_row = (
        uuid_blob(deployment.id),
        deployment.name,
        deployment.started_on.isoformat(sep=" "),
        None
        if deployment.ended_on is None
        else deployment.ended_on.isoformat(sep=" "),
        deployment.latitude,
        deployment.longitude,
    )
    recordings: List[tuple] = []
    outputs: List[tuple] = []
    detections: List[tuple] = []
    predicted_tags: List[tuple] = []

    for model_output in model_outputs:
        recording = model_output.recording
        recordings.append(
            (
                uuid_blob(recording.id),
                None if recording.path is None else str(recording.path),
                recording.created_on.isoformat(sep=" "),
                recording.duration,
                recording.samplerate,
                recording.audio_channels,
                uuid_blob(recording.deployment.id),
            )
        )
        outputs.append(
            (
                uuid_blob(model_output.id),
                model_output.name_model,
                uuid_blob(recording.id),
                model_output.created_on.isoformat(sep=" "),
            )
        )

        for tag in model_output.tags:
            predicted_tags.append(
                (
                    tag.tag.key,
                    tag.tag.value,
                    tag.confidence_score,
                    None,
                    uuid_blob(model_output.id),
                )
            )

        for detection in model_output.detections:
            detections.append(
                (
                    uuid_blob(detection.id),
                    ""
                    if detection.location is None
                    else detection.location.model_dump_json(),
                    detection.detection_score,
                    uuid_blob(model_output.id),
                )
            )

            for tag in detection.tags:
                predicted_tags.append(
                    (
                        tag.tag.key,
                        tag.tag.value,
                        tag.confidence_score,
                        uuid_blob(detection.id),
                        None,
                    )
                )

    return FlatRows(
        deployment=deployment_row,
        recordings=recordings,
        model_outputs=outputs,
        detections=detections,
        predicted_tags=predicted_tags,
    )


def initialise_sqlite_schema(connection: sqlite3.Connection) -> None:
    """Create a schema close to the current Pony-backed sqlite store."""
    connection.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE deployment (
            id BLOB PRIMARY KEY,
            name TEXT NOT NULL,
            started_on DATETIME NOT NULL UNIQUE,
            ended_on DATETIME,
            latitude REAL,
            longitude REAL
        );

        CREATE TABLE recording (
            id BLOB PRIMARY KEY,
            path TEXT UNIQUE,
            datetime DATETIME NOT NULL UNIQUE,
            duration_s REAL NOT NULL,
            samplerate_hz INTEGER NOT NULL,
            audio_channels INTEGER NOT NULL DEFAULT 1,
            deployment_id BLOB NOT NULL REFERENCES deployment(id)
        );

        CREATE TABLE model_output (
            id BLOB PRIMARY KEY,
            model_name TEXT NOT NULL,
            recording_id BLOB NOT NULL REFERENCES recording(id),
            created_on DATETIME NOT NULL
        );

        CREATE TABLE detection (
            id BLOB PRIMARY KEY,
            location TEXT,
            detection_score REAL NOT NULL,
            model_output_id BLOB NOT NULL REFERENCES model_output(id)
        );

        CREATE TABLE predicted_tag (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            confidence_score REAL NOT NULL,
            detection_id BLOB REFERENCES detection(id),
            model_output_id BLOB REFERENCES model_output(id)
        );
        """
    )


def bulk_insert_with_sqlite3(db_path: Path, rows: FlatRows) -> None:
    """Insert all rows with direct sqlite3 executemany calls."""
    if db_path.exists():
        db_path.unlink()

    connection = sqlite3.connect(db_path)
    try:
        initialise_sqlite_schema(connection)
        connection.execute("BEGIN")
        connection.execute(
            "INSERT INTO deployment (id, name, started_on, ended_on, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?)",
            rows.deployment,
        )
        connection.executemany(
            "INSERT INTO recording (id, path, datetime, duration_s, samplerate_hz, audio_channels, deployment_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            rows.recordings,
        )
        connection.executemany(
            "INSERT INTO model_output (id, model_name, recording_id, created_on) VALUES (?, ?, ?, ?)",
            rows.model_outputs,
        )
        connection.executemany(
            "INSERT INTO detection (id, location, detection_score, model_output_id) VALUES (?, ?, ?, ?)",
            rows.detections,
        )
        connection.executemany(
            "INSERT INTO predicted_tag (key, value, confidence_score, detection_id, model_output_id) VALUES (?, ?, ?, ?, ?)",
            rows.predicted_tags,
        )
        connection.commit()
    finally:
        connection.close()


def main() -> None:
    """Run the benchmark."""
    args = build_parser().parse_args()

    if args.recordings <= 0:
        raise SystemExit("--recordings must be greater than 0")
    if args.detections_per_output < 0:
        raise SystemExit("--detections-per-output must be 0 or greater")
    if args.tags_per_detection <= 0:
        raise SystemExit("--tags-per-detection must be greater than 0")
    if args.recording_tags < 0:
        raise SystemExit("--recording-tags must be 0 or greater")
    if args.read_limit <= 0:
        raise SystemExit("--read-limit must be greater than 0")
    if args.sample_size <= 0:
        raise SystemExit("--sample-size must be greater than 0")

    db_path = args.db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)

    created_db = False
    if db_path.exists() and not args.reuse_db:
        db_path.unlink()
    if not db_path.exists():
        created_db = True

    store = SqliteStore(db_path)
    deployment = data.Deployment(
        name="benchmark-deployment",
        started_on=dt.datetime(2024, 1, 1, 0, 0, 0),
    )
    store.store_deployment(deployment)

    base_time = dt.datetime(2024, 1, 1, 12, 0, 0)
    model_outputs: List[data.ModelOutput] = []
    results: List[BenchmarkResult] = []

    print("Benchmark configuration")
    print(f"db_path={db_path}")
    print(f"recordings={args.recordings}")
    print(f"detections_per_output={args.detections_per_output}")
    print(f"tags_per_detection={args.tags_per_detection}")
    print(f"recording_tags={args.recording_tags}")
    print()

    results.append(
        time_call(
            "build synthetic payloads",
            lambda: model_outputs.extend(
                make_model_output(
                    deployment=deployment,
                    recording_index=recording_index,
                    detections_per_output=args.detections_per_output,
                    tags_per_detection=args.tags_per_detection,
                    recording_tags=args.recording_tags,
                    base_time=base_time,
                )
                for recording_index in range(args.recordings)
            ),
            extra=(
                f"total_detections={args.recordings * args.detections_per_output}"
            ),
        )
    )

    write_times: List[float] = []
    for model_output in model_outputs:
        started = time.perf_counter()
        store.store_model_output(model_output)
        write_times.append(time.perf_counter() - started)

    total_write_seconds = sum(write_times)
    total_detections = args.recordings * args.detections_per_output
    results.append(
        BenchmarkResult(
            name="store_model_output total",
            seconds=total_write_seconds,
            extra=(
                f"per_output_mean={statistics.mean(write_times):.4f}s"
                f", per_output_p95={quantile(write_times, 0.95):.4f}s"
                f", detections_per_sec={safe_rate(total_detections, total_write_seconds):.1f}"
            ),
        )
    )

    if args.compare_sqlite3:
        sqlite_rows = prepare_sqlite_rows(deployment, model_outputs)
        sqlite_db_path = db_path.with_name(
            f"{db_path.stem}-sqlite3{db_path.suffix}"
        )
        sqlite_result = time_call(
            "sqlite3 bulk insert total",
            lambda: bulk_insert_with_sqlite3(sqlite_db_path, sqlite_rows),
        )
        sqlite_result.extra = (
            f"detections_per_sec={safe_rate(total_detections, sqlite_result.seconds):.1f}"
            f", speedup_vs_pony={safe_divide(total_write_seconds, sqlite_result.seconds):.2f}x"
        )
        results.append(sqlite_result)
        if not args.keep_db:
            sqlite_db_path.unlink(missing_ok=True)

    sample_size = min(args.sample_size, len(model_outputs))
    recording_ids = [
        model_output.recording.id
        for model_output in model_outputs[:sample_size]
    ]
    model_output_ids = [
        model_output.id for model_output in model_outputs[:sample_size]
    ]
    detection_ids = [
        detection.id
        for model_output in model_outputs[:sample_size]
        for detection in model_output.detections[:1]
    ]
    paths = [
        model_output.recording.path
        for model_output in model_outputs[:sample_size]
    ]
    paths = [path for path in paths if path is not None]

    results.append(
        time_call(
            "get_recordings(ids)",
            lambda: store.get_recordings(recording_ids),
            extra=f"sample_size={len(recording_ids)}",
        )
    )
    results.append(
        time_call(
            "get_recordings_by_path",
            lambda: store.get_recordings_by_path(paths),
            extra=f"sample_size={len(paths)}",
        )
    )
    results.append(
        time_call(
            "get_model_outputs(limit)",
            lambda: store.get_model_outputs(limit=args.read_limit),
            extra=f"limit={args.read_limit}",
        )
    )
    results.append(
        time_call(
            "get_detections(model_output_ids)",
            lambda: store.get_detections(model_output_ids=model_output_ids),
            extra=f"sample_size={len(model_output_ids)}",
        )
    )
    if detection_ids:
        results.append(
            time_call(
                "get_predicted_tags(detection_ids)",
                lambda: store.get_predicted_tags(detection_ids=detection_ids),
                extra=f"sample_size={len(detection_ids)}",
            )
        )

    results.append(
        time_call(
            "get_detections(score_gt=0.5)",
            lambda: store.get_detections(score_gt=0.5),
            extra="full table scan/filter",
        )
    )

    print_results(results)

    if created_db and not args.keep_db:
        db_path.unlink(missing_ok=True)


def quantile(values: Sequence[float], q: float) -> float:
    """Return a simple quantile for a non-empty sequence."""
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(q * (len(ordered) - 1)))
    return ordered[index]


def safe_rate(count: int, seconds: float) -> float:
    """Return count/seconds while handling zero safely."""
    if seconds == 0:
        return float("inf")
    return count / seconds


def safe_divide(numerator: float, denominator: float) -> float:
    """Return numerator/denominator while handling zero safely."""
    if denominator == 0:
        return float("inf")
    return numerator / denominator


if __name__ == "__main__":
    main()
