"""Test running the model of a recorded audio file"""

from acoupi.model import BatDetect2
from acoupi import types
from bat_detect import api

def test_model():
    """Test running the model"""

    recording = types.Recording(
            path='test', 
            duration=1, 
            samplerate=16000, 
            datetime=datetime.datetime.now()
        )
    model_run = BatDetect2(recording)
    assert model_run.detections