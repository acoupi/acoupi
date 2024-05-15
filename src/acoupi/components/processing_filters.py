"""Processing filters for the Acoupi project.

Processing filters are used to determine if a recording should be processed by
the model. This is useful for example if you want to only process recordings
that satisfy certain criteria, such as a minimum duration or that surpass a
certain amplitude threshold. This can be used to reduce the amount of
computational resources required to process a large number of recordings.

Processing filters are implemented as classes that inherit from
ProcessingFilter. The class should implement the should_process_recording
method, which takes a Recording object and returns a boolean indicating if the
recording should be processed by the model.

Keep in mind that the should_process_recording method is called for every
recording, so it should be as efficient as possible.
"""

from acoupi.components.types import ProcessingFilter, Recording

__all__ = [
    "TrivialProcessingFilter",
]


class TrivialProcessingFilter(ProcessingFilter):
    """A ProcessingFilter that always returns True."""

    def should_process_recording(self, recording: Recording) -> bool:
        """Determine if the recording should be processed by the model."""
        return True
