"""Test suite for system functions to manage worker scripts."""

import os
from pathlib import Path

import pytest

from acoupi.programs.workers import AcoupiWorker, WorkerConfig
from acoupi.system.scripts import write_workers_start_script


@pytest.fixture
def acoupi_home(tmp_path: Path) -> Path:
    """Fixture to set up ACOUPI_HOME environment variable."""
    acoupi_home = tmp_path / "acoupi"
    os.environ["ACOUPI_HOME"] = str(tmp_path / "acoupi")

    run_dir = acoupi_home / "run"
    run_dir.mkdir(parents=True)

    log_dir = acoupi_home / "log"
    log_dir.mkdir(parents=True)

    scripts_dir = acoupi_home / "scripts"
    scripts_dir.mkdir(parents=True)

    return acoupi_home


def test_write_workers_start_script_with_one_worker(acoupi_home: Path):
    """Test writing a workers start script with one worker."""
    # Arrange
    script_path = acoupi_home / "scripts" / "start_workers.sh"
    worker = AcoupiWorker(name="acoupi")
    config = WorkerConfig(workers=[worker])

    log_dir = acoupi_home / "log"
    run_dir = acoupi_home / "run"
    celery_bin = acoupi_home / "bin" / "celery"

    # Act
    write_workers_start_script(
        config,
        script_path,
        app_name="app",
        log_level="INFO",
        log_dir=log_dir,
        run_dir=run_dir,
        celery_bin=celery_bin,
    )

    # Assert
    assert script_path.exists()
    assert script_path.is_file()
    assert os.access(script_path, os.X_OK)

    expected_line = rf"""
    {celery_bin} \
    -A app \
    multi \
    start \
    acoupi \
    --loglevel=INFO \
    --pidfile={run_dir}/%n.pid \
    --logfile={log_dir}/%n%I.log
    """
    assert expected_line.strip() in script_path.read_text()


def test_write_workers_start_script_for_worker_with_queues(
    acoupi_home: Path,
):
    """Test writing a workers start script for a worker with queues."""
    # Arrange
    script_path = acoupi_home / "scripts" / "start_workers.sh"
    worker = AcoupiWorker(name="acoupi", queues=["default", "celery"])
    config = WorkerConfig(workers=[worker])

    log_dir = acoupi_home / "log"
    run_dir = acoupi_home / "run"
    celery_bin = acoupi_home / "bin" / "celery"

    # Act
    write_workers_start_script(
        config,
        script_path,
        app_name="app",
        log_level="INFO",
        log_dir=log_dir,
        run_dir=run_dir,
        celery_bin=celery_bin,
    )

    # Assert
    assert script_path.exists()
    assert script_path.is_file()
    assert os.access(script_path, os.X_OK)

    expected_line = rf"""
    {celery_bin} \
    -A app \
    multi \
    start \
    acoupi \
    -Q:acoupi default,celery \
    --loglevel=INFO \
    --pidfile={run_dir}/%n.pid \
    --logfile={log_dir}/%n%I.log
    """
    assert expected_line.strip() in script_path.read_text()


def test_write_workers_start_script_with_concurrency(
    acoupi_home: Path,
):
    """Test writing a workers start script with concurrency."""
    # Arrange
    script_path = acoupi_home / "scripts" / "start_workers.sh"
    worker = AcoupiWorker(name="acoupi", concurrency=2)
    config = WorkerConfig(workers=[worker])

    log_dir = acoupi_home / "log"
    run_dir = acoupi_home / "run"
    celery_bin = acoupi_home / "bin" / "celery"

    # Act
    write_workers_start_script(
        config,
        script_path,
        app_name="app",
        log_level="INFO",
        log_dir=log_dir,
        run_dir=run_dir,
        celery_bin=celery_bin,
    )

    # Assert
    assert script_path.exists()
    assert script_path.is_file()
    assert os.access(script_path, os.X_OK)

    expected_line = rf"""
    {celery_bin} \
    -A app \
    multi \
    start \
    acoupi \
    -c:acoupi 2 \
    --loglevel=INFO \
    --pidfile={run_dir}/%n.pid \
    --logfile={log_dir}/%n%I.log
    """
    assert expected_line.strip() in script_path.read_text()


def test_write_start_script_with_multiple_workers(
    acoupi_home: Path,
):
    """Test writing a workers start script with multiple workers."""
    # Arrange
    script_path = acoupi_home / "scripts" / "start_workers.sh"
    worker1 = AcoupiWorker(name="worker1")
    worker2 = AcoupiWorker(name="worker2", concurrency=2)
    worker3 = AcoupiWorker(name="worker3", queues=["queue"])
    config = WorkerConfig(workers=[worker1, worker2, worker3])

    log_dir = acoupi_home / "log"
    run_dir = acoupi_home / "run"
    celery_bin = acoupi_home / "bin" / "celery"

    # Act
    write_workers_start_script(
        config,
        script_path,
        app_name="app",
        log_level="INFO",
        log_dir=log_dir,
        run_dir=run_dir,
        celery_bin=celery_bin,
    )

    # Assert
    assert script_path.exists()
    assert script_path.is_file()
    assert os.access(script_path, os.X_OK)

    expected_line = rf"""
    {celery_bin} \
    -A app \
    multi \
    start \
    worker1 \
    worker2 \
    -c:worker2 2 \
    worker3 \
    -Q:worker3 queue \
    --loglevel=INFO \
    --pidfile={run_dir}/%n.pid \
    --logfile={log_dir}/%n%I.log
    """
    assert expected_line.strip() in script_path.read_text()
