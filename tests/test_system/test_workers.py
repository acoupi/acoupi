"""Test suite for system functions to manage worker scripts."""

import os

from acoupi.programs.workers import AcoupiWorker, WorkerConfig
from acoupi.system import Settings
from acoupi.system.scripts import write_workers_start_script


def test_write_workers_start_script_with_one_worker(settings: Settings):
    """Test writing a workers start script with one worker."""
    # Arrange
    worker = AcoupiWorker(name="acoupi")
    config = WorkerConfig(workers=[worker])

    celery_bin = settings.home / "bin" / "celery"

    script_path = settings.start_script_path

    # Act
    write_workers_start_script(
        config,
        settings,
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
    --pool=eventlet \
    --loglevel=INFO \
    --pidfile={settings.run_dir}/%n.pid \
    --logfile={settings.log_dir}/%n%I.log
    """
    assert expected_line.strip() in script_path.read_text()


def test_write_workers_start_script_for_worker_with_queues(
    settings: Settings,
):
    """Test writing a workers start script for a worker with queues."""
    # Arrange
    worker = AcoupiWorker(name="acoupi", queues=["default", "celery"])
    config = WorkerConfig(workers=[worker])

    script_path = settings.start_script_path
    celery_bin = settings.home / "bin" / "celery"

    # Act
    write_workers_start_script(
        config,
        settings,
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
    --pool=eventlet \
    --loglevel=INFO \
    --pidfile={settings.run_dir}/%n.pid \
    --logfile={settings.log_dir}/%n%I.log
    """
    assert expected_line.strip() in script_path.read_text()


def test_write_workers_start_script_with_concurrency(
    settings: Settings,
):
    """Test writing a workers start script with concurrency."""
    # Arrange
    worker = AcoupiWorker(name="acoupi", concurrency=2)
    config = WorkerConfig(workers=[worker])

    script_path = settings.start_script_path
    celery_bin = settings.home / "bin" / "celery"

    # Act
    write_workers_start_script(
        config,
        settings,
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
    --pool=eventlet \
    --loglevel=INFO \
    --pidfile={settings.run_dir}/%n.pid \
    --logfile={settings.log_dir}/%n%I.log
    """
    assert expected_line.strip() in script_path.read_text()


def test_write_start_script_with_multiple_workers(
    settings: Settings,
):
    """Test writing a workers start script with multiple workers."""
    # Arrange
    worker1 = AcoupiWorker(name="worker1")
    worker2 = AcoupiWorker(name="worker2", concurrency=2)
    worker3 = AcoupiWorker(name="worker3", queues=["queue"])
    config = WorkerConfig(workers=[worker1, worker2, worker3])

    script_path = settings.start_script_path
    celery_bin = settings.home / "bin" / "celery"

    # Act
    write_workers_start_script(
        config,
        settings,
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
    --pool=eventlet \
    --loglevel=INFO \
    --pidfile={settings.run_dir}/%n.pid \
    --logfile={settings.log_dir}/%n%I.log
    """
    assert expected_line.strip() in script_path.read_text()
