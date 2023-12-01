"""Acoupi detection and classification Test Model."""
from acoupi import data
from acoupi.components import types


class TestModel(types.Model):
    """Test Model to analyse the audio recording."""

    def run(self, recording: data.Recording) -> data.ModelOutput:
        """Run the model on the recording."""
        return data.ModelOutput(
            name_model="TestModel",
            recording=recording,
        )
