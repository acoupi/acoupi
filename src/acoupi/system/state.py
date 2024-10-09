"""Functions for accessing the state of the Acoupi system."""

from acoupi.system.constants import Settings


def is_configured(settings: Settings) -> bool:
    """Check if acoupi is configured."""
    return (
        settings.program_config_file.exists()
        and settings.program_file.exists()
        and settings.program_name_file.exists()
    )
