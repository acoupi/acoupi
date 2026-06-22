import os
import shutil
from pathlib import Path

import psutil

from acoupi import data


def get_remaining_storage(
    path: Path,
    name: str = "remaining_storage",
) -> data.Metric:
    """Return the remaining storage space for a path.

    Parameters
    ----------
    path : Path
        Path on the target filesystem.
    name : str, default="remaining_storage"
        Metric name to include in the returned object.

    Returns
    -------
    data.Metric
        Metric containing the available storage in bytes.
    """
    return data.Metric(
        name=name,
        value=shutil.disk_usage(path).free,
        unit="bytes",
    )


def get_used_storage(
    path: Path,
    name: str = "used_storage",
) -> data.Metric:
    """Return the used storage space for a path.

    Parameters
    ----------
    path : Path
        Path on the target filesystem.
    name : str, default="used_storage"
        Metric name to include in the returned object.

    Returns
    -------
    data.Metric
        Metric containing the used storage in bytes.
    """
    return data.Metric(
        name=name,
        value=shutil.disk_usage(path).used,
        unit="bytes",
    )


def get_free_memory(
    name: str = "free_memory",
) -> data.Metric:
    """Return the currently available system memory.

    Parameters
    ----------
    name : str, default="free_memory"
        Metric name to include in the returned object.

    Returns
    -------
    data.Metric
        Metric containing available memory in bytes.
    """
    mem_info = psutil.virtual_memory()
    return data.Metric(
        name=name,
        value=mem_info.available,
        unit="bytes",
    )


def consumed_memory(
    name: str = "consumed_memory",
) -> data.Metric:
    """Return the resident memory used by the current process.

    Parameters
    ----------
    name : str, default="consumed_memory"
        Metric name to include in the returned object.

    Returns
    -------
    data.Metric
        Metric containing process RSS memory in bytes.
    """
    pid = os.getpid()
    process = psutil.Process(pid)
    return data.Metric(
        name=name,
        value=process.memory_info().rss,
        unit="bytes",
    )


def get_cpu_usage(
    name: str = "cpu_usage",
) -> data.Metric:
    """Return the CPU usage of the current process.

    Parameters
    ----------
    name : str, default="cpu_usage"
        Metric name to include in the returned object.

    Returns
    -------
    data.Metric
        Metric containing process CPU usage as a percent.
    """
    pid = os.getpid()
    process = psutil.Process(pid)
    return data.Metric(
        name=name,
        value=process.cpu_percent(),
        unit="percent",
    )
