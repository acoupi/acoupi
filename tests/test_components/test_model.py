"""Test running the model of a recorded audio file."""

from pathlib import Path

from acoupi import data
from acoupi.components import types


class MockModel(types.Model):
    """Test Model to analyse the audio recording."""

    def run(self, recording: data.Recording) -> data.ModelOutput:
        """Run the model on the recording."""
        if not recording.path:
            return data.ModelOutput(
                name_model="TestModel",
                recording=recording,
            )

        detections = [
            data.PresenceDetection(
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


def test_model(deployment: data.Deployment):
    """Test running the model."""
    recording = data.Recording(
        path=Path("tests/data/test_ultrasonic.wav"),
        duration=1,
        samplerate=16000,
        created_on=data.utc_now(),
        deployment=deployment,
    )
    model = MockModel()
    results = model.run(recording)
    assert isinstance(results, data.ModelOutput)
