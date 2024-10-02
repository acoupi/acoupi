"""Test suite for acoupi program system module."""

import sys
from pathlib import Path

import pytest

from acoupi.programs.default import Program as SampleProgram
from acoupi.programs.test import TestProgram
from acoupi.system import Settings, exceptions, programs


def test_write_program_file_creates_a_file(settings: Settings):
    """Test write_program_file creates a file."""
    program_name = "test_program"
    programs.write_program_file(program_name, settings)
    program_file = settings.program_file
    assert program_file.exists()


def test_write_program_file_has_correct_program_name(settings: Settings):
    """Test write_program_file has correct program name."""
    program_name = "test_program"
    programs.write_program_file(
        program_name,
        settings,
    )

    program_name_file = settings.program_name_file
    program_file = settings.program_file
    line = f'program_name_file=Path("{str(program_name_file)}")'
    with open(program_file) as file:
        assert line in file.read()


def test_write_program_file_points_to_correct_config_file(settings: Settings):
    """Test write_program_file points to correct config file."""
    program_name = "test_program"
    programs.write_program_file(program_name, settings)

    config_file = settings.program_config_file
    program_file = settings.program_file

    line = f'config_file=Path("{config_file}")'
    with open(program_file) as file:
        assert line in file.read()


def test_can_load_the_test_program():
    """Test can load the test program."""
    program_class = programs.load_program_class("acoupi.programs.test")
    assert program_class == TestProgram


def test_can_load_the_acoupi_program():
    """Test can load the test program."""
    program_class = programs.load_program_class("acoupi.programs.default")
    assert program_class == SampleProgram


sample_program = """
from acoupi.programs import AcoupiProgram
from acoupi.programs.templates import BasicProgram, BasicProgramConfiguration


class Config(BasicProgramConfiguration):
    name: str = "test"


class Program(BasicProgram[Config]):
    config_schema = Config

    name = "test_program"
"""


def test_loads_correct_program_when_multiple_programs_exist(tmp_path: Path):
    program_file = tmp_path / "test_program.py"
    program_file.write_text(sample_program)
    sys.path.append(str(tmp_path))
    program_class = programs.load_program_class("test_program")
    assert program_class.__name__ == "Program"
    assert hasattr(program_class, "name")
    assert getattr(program_class, "name") == "test_program"


def test_load_program_fails_if_module_does_not_exist():
    """Test load_program fails if file does not exist."""
    with pytest.raises(exceptions.ProgramNotFoundError):
        programs.load_program_class("does.not.exist")


def test_load_program_fails_if_no_program_is_found_in_module():
    """Test load_program fails if no program is found in module."""
    with pytest.raises(exceptions.ProgramNotFoundError):
        programs.load_program_class("math")
