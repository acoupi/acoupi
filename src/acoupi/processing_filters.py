from acoupi.types import ProcessingFilter, Recording

__all__ = [
    "TrivialProcessingFilter",
]


class TrivialProcessingFilter(ProcessingFilter):
    """A ProcessingFilter that always returns True."""

    def should_process_recording(self, recording: Recording) -> bool:
        """Determine if the recording should be processed by the model"""
        return True
