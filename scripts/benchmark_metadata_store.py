"""Benchmark Acoupi metadata-store operations across deployment stages.

This script measures the three main database interactions used by the default
task pipeline:

1. ``recording_task`` style write via ``store.store_recording``
2. ``detection_task`` style write via ``store.store_model_outputs``
3. ``file_management_task`` style lookup via ``store.get_recordings_by_path``

Each operation is benchmarked against databases at different stages of a
deployment, from nearly empty to heavily populated.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sqlite3
import statistics
import time
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Callable, Iterable, List, Sequence, TypeVar

from acoupi import data
from acoupi.components.stores import SqliteStore


@dataclass
class BenchmarkResult:
    """Single benchmark measurement."""

    stage: str
    operation: str
    seconds: float
    extra: str = ""


@dataclass(frozen=True)
class StageDefinition:
    """Population size representing a deployment stage."""

    name: str
    existing_recordings: int
    detections_per_output: int


T = TypeVar("T")


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark metadata-store operations for recording, detection, "
            "and file-management task interactions across deployment stages."
        )
    )
    parser.add_argument(
        "--db-dir",
        type=Path,
        default=Path("/tmp/acoupi-benchmark-stages"),
        help="Directory where temporary stage databases are created.",
    )
    parser.add_argument(
        "--recording-batch-size",
        type=int,
        default=20,
        help="Number of new recordings to store for the recording_task benchmark.",
    )
    parser.add_argument(
        "--detection-batch-size",
        type=int,
        default=20,
        help="Number of model outputs to store for the detection_task benchmark.",
    )
    parser.add_argument(
        "--management-sample-size",
        type=int,
        default=20,
        help="Number of paths passed to get_recordings_by_path.",
    )
    parser.add_argument(
        "--query-repetitions",
        type=int,
        default=20,
        help="Number of times to repeat the get_recordings_by_path query.",
    )
    parser.add_argument(
        "--tags-per-detection",
        type=int,
        default=5,
        help="Number of predicted tags on each detection.",
    )
    parser.add_argument(
        "--recording-tags",
        type=int,
        default=0,
        help="Number of recording-level tags on each model output.",
    )
    parser.add_argument(
        "--keep-dbs",
        action="store_true",
        help="Keep generated sqlite databases after benchmarking.",
    )
    parser.add_argument(
        "--stages",
        type=str,
        default="",
        help=(
            "Comma-separated list of stages to run, for example 'empty,1d'. "
            "Default runs all stages."
        ),
    )
    return parser


RECORDINGS_PER_DAY = 24 * 4


def stage_definitions() -> List[StageDefinition]:
    """Return the default benchmark stages."""
    return [
        StageDefinition(
            name="empty",
            existing_recordings=0,
            detections_per_output=200,
        ),
        StageDefinition(
            name="1d",
            existing_recordings=RECORDINGS_PER_DAY,
            detections_per_output=200,
        ),
        StageDefinition(
            name="7d",
            existing_recordings=RECORDINGS_PER_DAY * 7,
            detections_per_output=200,
        ),
        StageDefinition(
            name="30d",
            existing_recordings=RECORDINGS_PER_DAY * 30,
            detections_per_output=200,
        ),
        StageDefinition(
            name="90d",
            existing_recordings=RECORDINGS_PER_DAY * 90,
            detections_per_output=200,
        ),
    ]


def select_stages(stage_filter: str) -> List[StageDefinition]:
    """Return the requested stages or all stages if no filter is provided."""
    stages = stage_definitions()
    if not stage_filter.strip():
        return stages

    requested = [
        name.strip() for name in stage_filter.split(",") if name.strip()
    ]
    stage_map = {stage.name: stage for stage in stages}
    unknown = [name for name in requested if name not in stage_map]
    if unknown:
        available = ", ".join(stage_map)
        raise SystemExit(
            "Unknown stage(s): "
            + ", ".join(unknown)
            + f". Available stages: {available}"
        )

    return [stage_map[name] for name in requested]


def make_tag(index: int, score: float) -> data.PredictedTag:
    """Create a deterministic predicted tag."""
    return data.PredictedTag(
        tag=data.Tag(key="species", value=f"species_{index % 10}"),
        confidence_score=score,
    )


def make_detection(index: int, tags_per_detection: int) -> data.Detection:
    """Create a deterministic synthetic detection."""
    tags = [
        make_tag(index + tag_index, max(0.0, 0.99 - 0.01 * tag_index))
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


def make_recording(
    deployment: data.Deployment,
    recording_index: int,
    base_time: dt.datetime,
) -> data.Recording:
    """Create one synthetic recording."""
    created_on = base_time + dt.timedelta(seconds=recording_index)
    return data.Recording(
        created_on=created_on,
        duration=3.0,
        samplerate=48_000,
        deployment=deployment,
        path=Path(f"/tmp/acoupi/recording_{recording_index:08d}.wav"),
        audio_channels=1,
    )


def make_model_output(
    recording: data.Recording,
    recording_index: int,
    detections_per_output: int,
    tags_per_detection: int,
    recording_tags: int,
) -> data.ModelOutput:
    """Create one synthetic model output for a recording."""
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
        created_on=recording.created_on,
    )


def time_call(
    stage: str,
    operation: str,
    func: Callable[[], object],
    extra: str = "",
) -> BenchmarkResult:
    """Measure one callable."""
    start = time.perf_counter()
    func()
    end = time.perf_counter()
    return BenchmarkResult(
        stage=stage, operation=operation, seconds=end - start, extra=extra
    )


def time_repeated_calls(
    stage: str,
    operation: str,
    calls: Sequence[Callable[[], object]],
    extra: str = "",
) -> BenchmarkResult:
    """Measure repeated single-operation calls and report summary stats."""
    durations = []
    for call in calls:
        start = time.perf_counter()
        call()
        durations.append(time.perf_counter() - start)

    summary = [
        f"n={len(durations)}",
        f"mean={statistics.mean(durations):.4f}s",
        f"std={statistics.pstdev(durations):.4f}s",
    ]
    if extra:
        summary.append(extra)

    return BenchmarkResult(
        stage=stage,
        operation=operation,
        seconds=sum(durations),
        extra=", ".join(summary),
    )


def print_results(results: Sequence[BenchmarkResult]) -> None:
    """Print benchmark results grouped by stage."""
    stage_width = max(len(result.stage) for result in results)
    op_width = max(len(result.operation) for result in results)
    for result in results:
        extra = f" | {result.extra}" if result.extra else ""
        print(
            f"{result.stage:<{stage_width}} | {result.operation:<{op_width}} : "
            f"{result.seconds:>9.4f} s{extra}"
        )


def chunked(values: Sequence[T], size: int) -> Iterable[Sequence[T]]:
    """Yield slices of a sequence."""
    for start in range(0, len(values), size):
        yield values[start : start + size]


def bulk_seed_stage_data(
    db_path: Path,
    deployment: data.Deployment,
    recordings: Sequence[data.Recording],
    model_outputs: Sequence[data.ModelOutput],
) -> None:
    """Seed recordings and model outputs directly with sqlite bulk inserts."""
    recording_rows = [
        (
            recording.id.bytes,
            None if recording.path is None else str(recording.path),
            recording.created_on.isoformat(sep=" "),
            recording.duration,
            recording.samplerate,
            recording.audio_channels,
            deployment.id.bytes,
        )
        for recording in recordings
    ]

    model_output_rows = []
    detection_rows = []
    predicted_tag_rows = []

    for model_output in model_outputs:
        model_output_rows.append(
            (
                model_output.id.bytes,
                model_output.name_model,
                model_output.recording.id.bytes,
                model_output.created_on.isoformat(sep=" "),
            )
        )

        for tag in model_output.tags:
            predicted_tag_rows.append(
                (
                    tag.tag.key,
                    tag.tag.value,
                    tag.confidence_score,
                    None,
                    model_output.id.bytes,
                )
            )

        for detection in model_output.detections:
            detection_rows.append(
                (
                    detection.id.bytes,
                    ""
                    if detection.location is None
                    else detection.location.model_dump_json(),
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
                        None,
                    )
                )

    with sqlite3.connect(str(db_path)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN")
        try:
            if recording_rows:
                connection.executemany(
                    "INSERT INTO recording (id, path, datetime, duration_s, samplerate_hz, audio_channels, deployment_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    recording_rows,
                )
            if model_output_rows:
                connection.executemany(
                    "INSERT INTO model_output (id, model_name, recording_id, created_on) VALUES (?, ?, ?, ?)",
                    model_output_rows,
                )
            if detection_rows:
                connection.executemany(
                    "INSERT INTO detection (id, location, detection_score, model_output_id) VALUES (?, ?, ?, ?)",
                    detection_rows,
                )
            if predicted_tag_rows:
                connection.executemany(
                    "INSERT INTO predicted_tag (key, value, confidence_score, detection_id, model_output_id) VALUES (?, ?, ?, ?, ?)",
                    predicted_tag_rows,
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise


def populate_stage_database(
    store: SqliteStore,
    deployment: data.Deployment,
    stage: StageDefinition,
    tags_per_detection: int,
    recording_tags: int,
) -> List[data.ModelOutput]:
    """Populate one stage database with existing recordings and detections."""
    base_time = dt.datetime(2024, 1, 1, 12, 0, 0)
    recordings = [
        make_recording(deployment, recording_index, base_time)
        for recording_index in range(stage.existing_recordings)
    ]

    model_outputs = [
        make_model_output(
            recording=recording,
            recording_index=index,
            detections_per_output=stage.detections_per_output,
            tags_per_detection=tags_per_detection,
            recording_tags=recording_tags,
        )
        for index, recording in enumerate(recordings)
    ]

    bulk_seed_stage_data(
        db_path=store.db_path,
        deployment=deployment,
        recordings=recordings,
        model_outputs=model_outputs,
    )

    return model_outputs


def main() -> None:
    """Run the staged benchmark."""
    args = build_parser().parse_args()

    if args.recording_batch_size <= 0:
        raise SystemExit("--recording-batch-size must be greater than 0")
    if args.detection_batch_size <= 0:
        raise SystemExit("--detection-batch-size must be greater than 0")
    if args.management_sample_size <= 0:
        raise SystemExit("--management-sample-size must be greater than 0")
    if args.query_repetitions <= 0:
        raise SystemExit("--query-repetitions must be greater than 0")
    if args.tags_per_detection <= 0:
        raise SystemExit("--tags-per-detection must be greater than 0")
    if args.recording_tags < 0:
        raise SystemExit("--recording-tags must be 0 or greater")

    args.db_dir.mkdir(parents=True, exist_ok=True)
    results: List[BenchmarkResult] = []

    print("Benchmark configuration")
    print(f"db_dir={args.db_dir}")
    print(f"recording_batch_size={args.recording_batch_size}")
    print(f"detection_batch_size={args.detection_batch_size}")
    print(f"management_sample_size={args.management_sample_size}")
    print(f"query_repetitions={args.query_repetitions}")
    print(f"tags_per_detection={args.tags_per_detection}")
    print(f"recording_tags={args.recording_tags}")
    print(f"stages={args.stages or 'all'}")
    print()

    for stage in select_stages(args.stages):
        print(f"Starting stage {stage}")

        db_path = args.db_dir / f"metadata-{stage.name}.db"
        if db_path.exists():
            db_path.unlink()

        print("Populating stage database...", end="")
        store = SqliteStore(db_path)
        deployment = data.Deployment(
            name=f"benchmark-{stage.name}",
            started_on=dt.datetime(2024, 1, 1, 0, 0, 0)
            + dt.timedelta(days=len(results)),
        )
        store.store_deployment(deployment)
        existing_outputs = populate_stage_database(
            store=store,
            deployment=deployment,
            stage=stage,
            tags_per_detection=args.tags_per_detection,
            recording_tags=args.recording_tags,
        )
        print(" done")

        base_index = stage.existing_recordings
        new_recordings = [
            make_recording(
                deployment=deployment,
                recording_index=base_index + index,
                base_time=dt.datetime(2024, 1, 1, 12, 0, 0),
            )
            for index in range(args.recording_batch_size)
        ]
        new_outputs = [
            make_model_output(
                recording=recording,
                recording_index=base_index + index,
                detections_per_output=stage.detections_per_output,
                tags_per_detection=args.tags_per_detection,
                recording_tags=args.recording_tags,
            )
            for index, recording in enumerate(new_recordings)
        ]

        print("Testing store recording")
        results.append(
            time_repeated_calls(
                stage=stage.name,
                operation="recording_task store_recording",
                calls=[
                    partial(store.store_recording, recording)
                    for recording in new_recordings
                ],
                extra=f"batch_size={len(new_recordings)}",
            )
        )

        print("Testing store model output")
        detection_batch = new_outputs[: args.detection_batch_size]
        results.append(
            time_repeated_calls(
                stage=stage.name,
                operation="detection_task store_model_output",
                calls=[
                    partial(store.store_model_output, model_output)
                    for model_output in detection_batch
                ],
                extra=(
                    f"batch_size={len(detection_batch)}, total_detections="
                    f"{len(detection_batch) * stage.detections_per_output}"
                ),
            )
        )

        all_outputs = existing_outputs + detection_batch
        sample_size = min(args.management_sample_size, len(all_outputs))
        sample_paths = [
            model_output.recording.path
            for model_output in all_outputs[:sample_size]
            if model_output.recording.path is not None
        ]

        print(f"Testing get {len(sample_paths)} recordings by path")
        results.append(
            time_repeated_calls(
                stage=stage.name,
                operation="file_management_task get_recordings_by_path",
                calls=[
                    partial(store.get_recordings_by_path, paths=sample_paths)
                    for _ in range(args.query_repetitions)
                ],
                extra=(
                    f"sample_size={len(sample_paths)}, "
                    f"query_repetitions={args.query_repetitions}"
                ),
            )
        )

        if not args.keep_dbs:
            db_path.unlink(missing_ok=True)

    print_results(results)


if __name__ == "__main__":
    main()
