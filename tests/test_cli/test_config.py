"""Test suite for the config commands."""

import json

from click.testing import CliRunner

from acoupi.cli import acoupi
from acoupi.system.constants import Settings


def test_the_config_command_shows_help(settings: Settings):
    """Test that the config command shows help."""
    runner = CliRunner()
    result = runner.invoke(acoupi, ["config"], obj={"settings": settings})
    assert result.exit_code == 0
    assert "Usage: acoupi config" in result.output


def test_config_get_fails_if_acoupi_has_not_been_setup(
    settings: Settings,
):
    """Test that the config subcommand fails if acoupi has not been setup."""
    runner = CliRunner()
    result = runner.invoke(
        acoupi,
        ["config", "get"],
        obj={"settings": settings},
    )
    assert result.exit_code == 1
    assert "Acoupi is not setup. Run `acoupi setup` first." in result.output


def test_can_get_the_current_configuration(settings: Settings):
    """Test that the config show command works."""
    runner = CliRunner()

    # Setup acoupi
    runner.invoke(
        acoupi,
        [
            "setup",
            "--program",
            "acoupi.programs.test",
            "--name",
            "test_program",
        ],
        obj={"settings": settings},
    )

    # Get the configuration
    result = runner.invoke(
        acoupi,
        ["config", "get", "--no-color"],
        obj={"settings": settings},
    )
    assert result.exit_code == 0
    assert '"name": "test_program"' in result.output


def test_can_set_configuration(settings: Settings):
    """Test that the config set command works."""
    runner = CliRunner()

    # Setup acoupi
    runner.invoke(
        acoupi,
        [
            "setup",
            "--program",
            "acoupi.programs.test",
            "--name",
            "test_program",
        ],
        obj={"settings": settings},
    )

    # Set the configuration
    result = runner.invoke(
        acoupi,
        ["config", "set", "--field", "name", "new_name"],
        obj={"settings": settings},
    )
    assert result.exit_code == 0

    assert json.loads(settings.program_config_file.read_text()) == {
        "name": "new_name"
    }

    # Get the configuration
    result = runner.invoke(
        acoupi,
        ["config", "get", "--no-color"],
        obj={"settings": settings},
    )
    assert result.exit_code == 0
    assert '"name": "new_name"' in result.output
