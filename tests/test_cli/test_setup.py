"""Test suite for the setup command."""

import pytest
from click.testing import CliRunner

from acoupi.cli import acoupi
from acoupi.system import scripts


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


def test_can_run_without_arguments():
    """Test that the setup command can be run without arguments."""
    runner = CliRunner()
    result = runner.invoke(acoupi, ["setup"])
    assert result.exit_code == 0


def test_setup_fails_if_program_not_found():
    """Test that the setup command fails if the program is not found."""
    runner = CliRunner()
    result = runner.invoke(acoupi, ["setup", "--program", "notfound"])
    assert result.exit_code == 1
