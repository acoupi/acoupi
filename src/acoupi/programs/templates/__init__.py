"""Acoupi program templates.

This module provides base classes and configuration schemas to simplify the
creation of Acoupi programs.

Available Templates:

- **Basic Program:** Provides a foundation for building Acoupi programs,
  including features for audio recording, metadata storage, and file management.
  - Base class: `BasicProgram`
  - Configuration schema: `BasicProgramConfiguration`
- **Messaging Program:** Extends the `BasicProgram` with messaging
  capabilities, enabling programs to send messages and heartbeats via HTTP or
  MQTT.
  - Base class: `MessagingProgram`
  - Configuration schema: `MessagingProgramConfiguration`
- **Detection Program:**  Extends the `MessagingProgram` with audio detection
  capabilities, allowing programs to run detection models on recordings and
  generate messages based on the results.
  - Base class: `DetectionProgram`
  - Configuration schema: `DetectionProgramConfiguration`

Each template includes a base class that provides core functionality and a
configuration schema to define the program's settings.

For detailed usage instructions, customization options, and examples, refer
to the individual template documentation.
"""

from acoupi.programs.templates.basic import (
    AudioConfiguration,
    BasicProgram,
    BasicProgramConfiguration,
    PathsConfiguration,
)
from acoupi.programs.templates.detection import (
    DetectionProgram,
    DetectionProgramConfiguration,
)
from acoupi.programs.templates.messaging import (
    MessagingConfig,
    MessagingProgram,
    MessagingProgramConfiguration,
)

__all__ = [
    "AudioConfiguration",
    "BasicProgram",
    "BasicProgram",
    "BasicProgramConfiguration",
    "DetectionProgram",
    "DetectionProgramConfiguration",
    "MessagingConfig",
    "MessagingProgram",
    "MessagingProgramConfiguration",
    "PathsConfiguration",
]
