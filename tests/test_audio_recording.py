"""Test the recording of an audio files"""

from acoupi.config import DEFAULT_RECORDING_DURATION, DEFAULT_SAMPLE_RATE, DEFAULT_AUDIO_CHANNELS, DEFAULT_CHUNK_SIZE
from acoupi.audio_recording import PyAudioRecorder

def test_audio_recording():
    """Test the audio file recording."""
    recorder = PyAudioRecorder(duration=DEFAULT_RECORDING_DURATION, 
                               sample_rate=DEFAULT_SAMPLE_RATE,
                               channels=DEFAULT_AUDIO_CHANNELS, 
                               chunk=DEFAULT_CHUNK_SIZE)

    # record audio
    recording = recorder.record()
    assert recorder.record(recording) 
