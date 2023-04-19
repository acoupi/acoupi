import datetime
import tempfile
from tempfile import TemporaryFile, NamedTemporaryFile
import pyaudio
import wave 
import sounddevice
import yaml
from typing import Optional, List, Dict
from dataclasses import dataclass


"""For Audio Recording"""
from config import DEFAULT_RECORDING_DURATION, DEFAULT_SAMPLE_RATE, DEFAULT_AUDIO_CHANNELS, DEFAULT_CHUNK_SIZE, DEVICE_INDEX
from acoupi_types import Deployment, Recording, AudioRecorder
"""For Audio Processing"""
from bat_detect import api
from acoupi_types import Model, Detection
""" Cleaning Model Output """
from config import DETECTION_THRESHOLD


## --------------- STEP 1 : Record Audio Files ------------------ ##
class PyAudioRecorder(AudioRecorder):
#class PyAudioRecorder(AudioRecorder):
    """An AudioRecorder that records a 3 second audio file."""

    def __init__(self, duration: float = DEFAULT_RECORDING_DURATION, 
                sample_rate: float = DEFAULT_SAMPLE_RATE, 
                channels: int = DEFAULT_AUDIO_CHANNELS, 
                chunk: int = DEFAULT_CHUNK_SIZE,
                device_index: int = DEVICE_INDEX): 

        # Audio Duration
        self.duration = duration
       
        # Audio Microphone Parameters
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk = chunk
        self.device_index = device_index


    #def record_audio(self,device_index) -> Recording:
    def record(self) -> Recording:
        """Record a 3 second temporary audio file at 192KHz. Return the temporary path of the file."""       


        #self.datetime = datetime.datetime.now().strftime('%Y%m%d-%H%M%S') 
        self.datetime = datetime.datetime.now()
        
        #Create a temporary file to record audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audiof:
            
            # Get the temporary file path from the created temporary audio file
            temp_audio_path = temp_audiof.name
            print(f"New Audio File: {temp_audio_path}")

            #Create an new instace of PyAudio
            p = pyaudio.PyAudio()
        
            #Open new audio stream to start recording
            stream = p.open(format=pyaudio.paInt16,
                            channels=self.channels,
                            rate=self.sample_rate,
                            input=True,
                            frames_per_buffer=self.chunk,
                            input_device_index=self.device_index)

            #Initialise array to store audio frames
            frames = []
            for i in range(0, int(self.sample_rate/self.chunk*self.duration)):
                data = stream.read(self.chunk)
                frames.append(data)

            #Stop Recording and close the port interface
            stream.stop_stream()
            stream.close()
            p.terminate()

            #Create a WAV file to write the audio data
            temp_audio_file = wave.open(temp_audio_path, 'wb')
            temp_audio_file.setnchannels(self.channels)
            temp_audio_file.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            temp_audio_file.setframerate(self.sample_rate)

            # Write the audio data to the temporary file
            temp_audio_file.writeframes(b''.join(frames))    
            temp_audio_file.close()

            # Create a Recording object and return it
            recording = Recording(path=temp_audio_path, datetime=self.datetime, duration=self.duration, samplerate=self.sample_rate)
            return recording



## --------------- STEP 2 : Run BatDetect2 Model ------------------ ##
class BatDetect2(Model):

    "BatDetect2 Model to analyse the audio recording"
    
    def __init__(self, recording: Recording):

        self.recording = recording

    def run(self, recording) -> List[Detection]:

        # Get the audio path of the recorded file
        audio_file_path = recording.path
        print(f"Audio file Path input model: {audio_file_path}")
        # Load the audio rile and compute spectrograms
        audio = api.load_audio(audio_file_path)
        spec = api.generate_spectrogram(audio)

        # And process the audio or the spectrogram with the model
        #detections, features, spec = api.process_audio(audio)
        detections, features = api.process_spectrogram(spec)

        return detections


## --------------- STEP 3 : Post Processing Audio ------------------ ##

class CleanModelOutput():

    def __init__(self, detections: Detection, threshold: float = DETECTION_THRESHOLD):

       self.detections = detections
       self.threshold = threshold


    def getDetection_aboveThreshold(self):
        
        # Iterate through all detections - Keep only the one above threshold
        keep_detections = [ann for ann in self.detections if ann['det_prob'] > self.threshold]

        return keep_detections


## --------------- STEP 4 : Save Processed Audio Recordings & Detections ------------------ ##

class SaveData():

    def __init__(self, detections:keep_detections):
        
        self.detections = keep_detections


    def save_recordings(self):
        return 
    
    def save_detections(self):
        return
