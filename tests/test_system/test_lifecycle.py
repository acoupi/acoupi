import pytest

from acoupi.system import Settings, exceptions, lifecycle, programs


def test_setup_program_creates_all_the_required_files(
    settings: Settings,
):
    lifecycle.setup_program(
        settings,
        program_name="acoupi.programs.test",
        prompt=False,
    )

    assert settings.home.exists()
    assert settings.program_file.exists()

    # The program name is stored in a file
    assert settings.program_name_file.exists()
    assert settings.program_name_file.read_text() == "acoupi.programs.test"

    # Check that configurations are created
    assert settings.program_config_file.exists()
    assert settings.celery_config_file.exists()

    # Check that scripts are created
    assert settings.beat_script_path.exists()
    assert settings.start_script_path.exists()
    assert settings.stop_script_path.exists()
    assert settings.restart_script_path.exists()


def test_start_program_cleans_deployment_if_failure_before_start(
    settings: Settings,
    monkeypatch,
):
    def mock_load_program(_: Settings):
        raise exceptions.InvalidProgramError(program="test")

    monkeypatch.setattr(
        programs,
        "load_program",
        mock_load_program,
    )

    with pytest.raises(exceptions.InvalidProgramError):
        lifecycle.start_program(settings, name="test")

    assert not settings.deployment_file.exists()
