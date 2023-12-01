"""Test running the model of a recorded audio file."""
import datetime
from pathlib import Path

from acoupi import data
from acoupi.components.models.model_test import TestModel


def test_model(deployment: data.Deployment):
    """Test running the model."""
    recording = data.Recording(
        path=Path("tests/data/test_ultrasonic.wav"),
        duration=1,
        samplerate=16000,
        datetime=datetime.datetime.now(),
        deployment=deployment,
    )
    model = TestModel()
    results = model.run(recording)
    assert isinstance(results, data.ModelOutput)
