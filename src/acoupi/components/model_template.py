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
                detection_score=0.9,
                location=data.BoundingBox.from_coordinates(
                    start_time=0,
                    low_freq=4000,
                    end_time=1,
                    high_freq=8000,
                ),
                tags=[
                    data.PredictedTag(
                        tag=data.Tag(
                            key="species",
                            value="scientific_name",
                        ),
                        confidence_score=0.9,
                    ),
                ],
            )
        ]

        return data.ModelOutput(
            name_model="TestModel",
            recording=recording,
            detections=detections,
        )
