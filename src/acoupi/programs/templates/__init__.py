"""Acoupi program templates.

This module provides templates to simplify the creation of Acoupi programs.

Features:

- **Program Mixins:**  These class mixins add functionality to your programs,
  such as messaging capabilities. Simply inherit from the mixin to integrate
  its features into your program.

- **Configuration Schemas:**  Pre-built configuration schemas ensure
  compatibility with Acoupi templates and provide a foundation for defining
  your program's configuration structure.

For detailed usage and examples, refer to the individual template documentation.
"""

from acoupi.programs.templates.basic import (
    BasicConfiguration,
    BasicProgramMixin,
    PathsConfiguration,
)
from acoupi.programs.templates.messaging import (
    MessagingConfig,
    MessagingConfigMixin,
    MessagingProgramMixin,
)

__all__ = [
    "BasicConfiguration",
    "BasicProgramMixin",
    "MessagingConfig",
    "PathsConfiguration",
    "MessagingProgramMixin",
    "MessagingConfigMixin",
]
