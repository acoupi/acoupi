"""Test suite for the CLI task commands."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from acoupi import system
from acoupi.cli import acoupi


@pytest.fixture(autouse=True)
def setup_program(settings: system.Settings):
    system.setup_program(settings, "acoupi.programs.test", prompt=False)


def test_can_get_the_full_list_of_test_program_tasks(
    settings: system.Settings,
):
    runner = CliRunner()
    result = runner.invoke(
        acoupi,
        ["task", "list"],
        obj={"settings": settings},
    )
    assert result.exit_code == 0
    assert "test_task" in result.output


def test_can_save_the_task_profile_to_a_file(
    settings: system.Settings,
    tmp_path: Path,
):
    runner = CliRunner()
    profile_path = tmp_path / "profile.prof"
    result = runner.invoke(
        acoupi,
        ["task", "profile", "test_task", "--output", str(profile_path)],
        obj={"settings": settings},
    )
    assert result.exit_code == 0
    assert profile_path.exists()
