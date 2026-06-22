import datetime
from collections import namedtuple
from unittest.mock import Mock

from acoupi import data
from acoupi.devices import metrics


class TestGetRemainingStorage:
    def test_returns_metric(self, monkeypatch, patched_now):
        """Return a storage metric containing free bytes."""
        now = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
        patched_now(now)
        usage = namedtuple("usage", ["total", "used", "free"])(100, 40, 60)
        monkeypatch.setattr(metrics.shutil, "disk_usage", lambda path: usage)

        metric = metrics.get_remaining_storage(path=Mock())

        assert metric == data.Metric(
            name="remaining_storage",
            value=60,
            unit="bytes",
            captured_on=now,
        )


class TestGetUsedStorage:
    def test_returns_metric(self, monkeypatch, patched_now):
        """Return a storage metric containing used bytes."""
        now = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
        patched_now(now)
        usage = namedtuple("usage", ["total", "used", "free"])(100, 40, 60)
        monkeypatch.setattr(metrics.shutil, "disk_usage", lambda path: usage)

        metric = metrics.get_used_storage(path=Mock())

        assert metric == data.Metric(
            name="used_storage",
            value=40,
            unit="bytes",
            captured_on=now,
        )


class TestGetFreeMemory:
    def test_returns_metric(self, monkeypatch, patched_now):
        """Return a memory metric containing available bytes."""
        now = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
        patched_now(now)
        memory = Mock(available=128)
        monkeypatch.setattr(metrics.psutil, "virtual_memory", lambda: memory)

        metric = metrics.get_free_memory()

        assert metric == data.Metric(
            name="free_memory",
            value=128,
            unit="bytes",
            captured_on=now,
        )


class TestConsumedMemory:
    def test_returns_metric(self, monkeypatch, patched_now):
        """Return a memory metric containing process RSS bytes."""
        now = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
        patched_now(now)
        process = Mock()
        process.memory_info.return_value = Mock(rss=256)
        monkeypatch.setattr(metrics.os, "getpid", lambda: 123)
        monkeypatch.setattr(metrics.psutil, "Process", lambda pid: process)

        metric = metrics.consumed_memory()

        assert metric == data.Metric(
            name="consumed_memory",
            value=256,
            unit="bytes",
            captured_on=now,
        )


class TestGetCpuUsage:
    def test_returns_metric(self, monkeypatch, patched_now):
        """Return a CPU metric containing process usage percent."""
        now = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
        patched_now(now)
        process = Mock()
        process.cpu_percent.return_value = 12.5
        monkeypatch.setattr(metrics.os, "getpid", lambda: 123)
        monkeypatch.setattr(metrics.psutil, "Process", lambda pid: process)

        metric = metrics.get_cpu_usage()

        assert metric == data.Metric(
            name="cpu_usage",
            value=12.5,
            unit="percent",
            captured_on=now,
        )
