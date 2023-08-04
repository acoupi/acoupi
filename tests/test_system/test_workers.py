"""Test suite for system functions to manage worker scripts."""


import os
from pathlib import Path

from acoupi.programs.workers import AcoupiWorker, WorkerConfig
from acoupi.system.workers import write_workers_start_script


def test_write_workers_start_script_with_one_worker(tmp_path: Path):
    """Test writing a workers start script with one worker."""
    # Arrange
    script_path = tmp_path / "start_workers.sh"
    worker = AcoupiWorker(name="acoupi")
    config = WorkerConfig(workers=[worker])

    # Act
    write_workers_start_script(
        config,
        script_path,
    )

    # Assert
    assert script_path.exists()
    assert script_path.is_file()
    assert os.access(script_path, os.X_OK)

    expected_line = r"""
    ${CELERY_BIN} \
    -A ${CELERY_APP} \
    multi \
    start \
    acoupi \
    --loglevel=${CELERYD_LOG_LEVEL} \
    --pidfile=${CELERYD_PID_FILE} \
    --logfile=${CELERYD_LOG_FILE}
    """
    assert expected_line.strip() in script_path.read_text()


def test_write_workers_start_script_for_worker_with_queues(
    tmp_path: Path,
):
    """Test writing a workers start script for a worker with queues."""
    # Arrange
    script_path = tmp_path / "start_workers.sh"
    worker = AcoupiWorker(name="acoupi", queues=["default", "celery"])
    config = WorkerConfig(workers=[worker])

    # Act
    write_workers_start_script(
        config,
        script_path,
    )

    # Assert
    assert script_path.exists()
    assert script_path.is_file()
    assert os.access(script_path, os.X_OK)

    expected_line = r"""
    ${CELERY_BIN} \
    -A ${CELERY_APP} \
    multi \
    start \
    acoupi \
    -Q:acoupi default,celery \
    --loglevel=${CELERYD_LOG_LEVEL} \
    --pidfile=${CELERYD_PID_FILE} \
    --logfile=${CELERYD_LOG_FILE}
    """
    assert expected_line.strip() in script_path.read_text()


def test_write_workers_start_script_with_concurrency(
    tmp_path: Path,
):
    """Test writing a workers start script with concurrency."""
    # Arrange
    script_path = tmp_path / "start_workers.sh"
    worker = AcoupiWorker(name="acoupi", concurrency=2)
    config = WorkerConfig(workers=[worker])

    # Act
    write_workers_start_script(
        config,
        script_path,
    )

    # Assert
    assert script_path.exists()
    assert script_path.is_file()
    assert os.access(script_path, os.X_OK)

    expected_line = r"""
    ${CELERY_BIN} \
    -A ${CELERY_APP} \
    multi \
    start \
    acoupi \
    -c:acoupi 2 \
    --loglevel=${CELERYD_LOG_LEVEL} \
    --pidfile=${CELERYD_PID_FILE} \
    --logfile=${CELERYD_LOG_FILE}
    """
    assert expected_line.strip() in script_path.read_text()



def test_write_start_script_with_multiple_workers(
    tmp_path: Path,
):
    """Test writing a workers start script with multiple workers."""
    # Arrange
    script_path = tmp_path / "start_workers.sh"
    worker1 = AcoupiWorker(name="worker1")
    worker2 = AcoupiWorker(name="worker2", concurrency=2)
    worker3 = AcoupiWorker(name="worker3", queues=["queue"])
    config = WorkerConfig(workers=[worker1, worker2, worker3])

    # Act
    write_workers_start_script(
        config,
        script_path,
    )

    # Assert
    assert script_path.exists()
    assert script_path.is_file()
    assert os.access(script_path, os.X_OK)

    expected_line = r"""
    ${CELERY_BIN} \
    -A ${CELERY_APP} \
    multi \
    start \
    worker1 \
    worker2 \
    -c:worker2 2 \
    worker3 \
    -Q:worker3 queue \
    --loglevel=${CELERYD_LOG_LEVEL} \
    --pidfile=${CELERYD_PID_FILE} \
    --logfile=${CELERYD_LOG_FILE}
    """
    assert expected_line.strip() in script_path.read_text()
