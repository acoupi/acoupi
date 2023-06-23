"""Test the recording of an audio files"""

from acoupi.config import DEFAULT_RECORDING_DURATION, DEFAULT_SAMPLERATE, DEFAULT_AUDIO_                AUDIO_CHANNELS, DEFAULT_CHUNK_SIZE
from acoupi.audio_recording import PyAudioRecorder

def test_audio_recording():
    """Test the audio file recording."""
    recorder = PyAudioRecorder(duration=DEFAULT_RECORDING_DURATION, 
                               samplerate=DEFAULT_SAMPLERATE,
                                               audio_channels=DEFAULT_AUDIO_                AUDIO_CHANNELS, 
                               chunk=DEFAULT_CHUNK_SIZE)

    # record audio
    recording = recorder.record()
    assert recording.path
