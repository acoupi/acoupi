""" Run BatDetect2 Model """
from typing import List, Dict
from batdetect2 import api

#from acoupi.types import Model, Recording, Detection

from acoupi_types import Model, Recording, Detection


class BatDetect2(Model):

    "BatDetect2 Model to analyse the audio recording"
    
    #def __init__(self, recording: Recording):

        #self.recording = recording

    def run(self, recording) -> List[Detection]:

        # Get the audio path of the recorded file
        audio_file_path = recording.path
        #print(f"Audio file Path input model: {audio_file_path}")
        # Load the audio rile and compute spectrograms
        audio = api.load_audio(audio_file_path)
        print(f"Audio Loaded in Model: {audio}")
        spec = api.generate_spectrogram(audio)

        # And process the audio or the spectrogram with the model
        #detections, features, spec = api.process_audio(audio)
        detections, features = api.process_spectrogram(spec)
        print(f"Detections Return from Model: {detections}")

        return detections
