"""Test suite for acoupi program system module."""

from pathlib import Path

import pytest

from acoupi.programs.test import TestProgram
from acoupi.system import programs


def test_write_program_file_creates_a_file(tmp_path: Path):
    """Test write_program_file creates a file."""
    program_file = tmp_path / "program.py"
    program_name = "test_program"
    programs.write_program_file(program_name, program_file=program_file)
    assert program_file.exists()


def test_write_program_file_has_correct_program_name(tmp_path: Path):
    """Test write_program_file has correct program name."""
    program_file = tmp_path / "program.py"
    program_name = "test_program"
    programs.write_program_file(program_name, program_file=program_file)

    line = f'program_name="{program_name}"'
    with open(program_file) as file:
        assert line in file.read()


def test_write_program_file_points_to_correct_config_file(tmp_path: Path):
    """Test write_program_file points to correct config file."""
    program_file = tmp_path / "program.py"
    program_name = "test_program"
    config_file = tmp_path / "config.json"
    programs.write_program_file(
        program_name, program_file=program_file, config_file=config_file
    )

    line = f'config_file="{config_file}"'
    with open(program_file) as file:
        assert line in file.read()


def test_can_load_the_test_program():
    """Test can load the test program."""
    program_class = programs.load_program("acoupi.programs.test")
    assert program_class == TestProgram


def test_load_program_fails_if_module_does_not_exist():
    """Test load_program fails if file does not exist."""
    with pytest.raises(ModuleNotFoundError):
        programs.load_program("does.not.exist")


def test_load_program_fails_if_no_program_is_found_in_module():
    """Test load_program fails if no program is found in module."""
    with pytest.raises(ValueError):
        programs.load_program("math")