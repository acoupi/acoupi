"""Test suite for the setup command."""
import pytest
from click.testing import CliRunner

from acoupi.cli import acoupi
from acoupi.system import Settings, scripts


@pytest.fixture(autouse=True)
def mock_celery_bin(monkeypatch):
    """Mock the celery binary."""

    def mock_get_celery_bin():
        return "/usr/bin/celery"

    monkeypatch.setattr(
        scripts,
        "get_celery_bin",
        mock_get_celery_bin,
    )


def test_can_run_check(settings: Settings):
    """Test that the setup command can be run without arguments."""
    runner = CliRunner()
    runner.invoke(
        acoupi,
        [
            "setup",
            "--program",
            "acoupi.programs.custom.test",
        ],
        obj={"settings": settings},
    )

    result = runner.invoke(acoupi, ["check"], obj={"settings": settings})
    assert result.exit_code == 0
    assert "Health checks passed" in result.output


def test_can_run_check_with_failed_checks(settings: Settings):
    """Test that the setup command can be run without arguments."""
    runner = CliRunner()
    runner.invoke(
        acoupi,
        [
            "setup",
            "--program",
            "acoupi.programs.custom.test",
            "--name",
            "test",
        ],
        obj={"settings": settings},
    )

    result = runner.invoke(acoupi, ["check"], obj={"settings": settings})
    assert result.exit_code == 1
    assert "name is not test_program" in result.output
