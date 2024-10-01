"""Acoupi Connected Program."""

from acoupi.programs import AcoupiProgram
from acoupi.programs.templates import (
    BasicConfiguration,
    BasicProgramMixin,
    MessagingConfigMixin,
    MessagingProgramMixin,
)


class ConfigSchema(BasicConfiguration, MessagingConfigMixin):
    """Configuration Schema for Connected Program."""


class Program(MessagingProgramMixin, BasicProgramMixin, AcoupiProgram):
    """Connected Program."""

    config_schema = ConfigSchema
