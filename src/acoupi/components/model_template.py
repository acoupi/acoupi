"""Acoupi detection and classification Test Model."""
from acoupi import data
from acoupi.components import types


class TestModel(types.Model):
    """Test Model to analyse the audio recording."""

    def run(self, recording: data.Recording) -> data.ModelOutput:
        """Run the model on the recording."""

        if not recording.path:
            return data.ModelOutput(
                name_model="TestModel",
                recording=recording,
            )

        detections = [
            data.Detection(
                probability="dectection_probability",
                location=data.BoundingBox.from_coordinates(
                    "start_time",
                    "low_freq",
                    "end_time",
                    "high_freq",
                ),
                tags=[
                    data.PredictedTag(
                        tag=data.Tag(
                            key="species",
                            value="scientific_name",
                        ),
                        probability="species_probabiliby",
                    ),
                ],
            )
        ]

        return data.ModelOutput(
            name_model="TestModel",
            recording=recording,
            detection=detections,
        )
