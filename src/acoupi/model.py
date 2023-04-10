""" Run BatDetect2 Model """
from typing import List, Dict
from bat_detect import api

#from acoupi.types import Model, Recording, Detection
#from acoupi.audio_recording import PyAudioRecorder

from acoupi_types import Model, Recording, Detection
#from audio_recording import PyAudioRecorder


class BatDetect2(Model):

    "BatDetect2 Model to analyse the audio recording"
    
    def __init__(self, recording: Recording):

        self.recording = recording

    def run(self, recording) -> List[Detection]:

        # Get the audio path of the recorded file
        audio_file_path = recording.path

        # Load the audio rile and compute spectrograms
        audio = api.load_audio(audio_file_path)
        spec = api.generate_spectrogram(audio)

        # And process the audio or the spectrogram with the model
        #detections, features, spec = api.process_audio(audio)
        detections, features = api.process_spectrogram(spec)

        return detections
