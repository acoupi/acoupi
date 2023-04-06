"""Definition of audio recorder"""
from datetime import datetime
import tempfile
from tempfile import TemporaryFile, NamedTemporaryFile
import pyaudio
import wave 
import yaml
import sounddevice
import yaml
from typing import Optional, List
from dataclasses import dataclass
#test

<<<<<<< HEAD
from acoupi.config import DEFAULT_RECORDING_DURATION, DEFAULT_SAMPLE_RATE, DEFAULT_AUDIO_CHANNELS, DEFAULT_CHUNK_SIZE
from acoupi.types import Recording, AudioRecorder
=======
#from acoupi.config import DEFAULT_RECORDING_DURATION, DEFAULT_SAMPLE_RATE, DEFAULT_AUDIO_CHANNELS, DEFAULT_CHUNK_SIZE
#from acoupi.types import Deployment, Recording, AudioRecorder
from config import DEFAULT_RECORDING_DURATION, DEFAULT_SAMPLE_RATE, DEFAULT_AUDIO_CHANNELS, DEFAULT_CHUNK_SIZE
from acoupi_types import Deployment, Recording, AudioRecorder
>>>>>>> 5b9b0012b92c0c4ead6cabcc49bacf109c1c1d80

# Load Configuration
with open("config.yaml") as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)

<<<<<<< HEAD
# class getDeployment_Info(Deployment):
#     def __init__(self,latitude: float,longitude:float):
#         self.lat = latitude
#         self.lon = longitude
# 
#     def read_deployment_config(self):
#         #cfg = ... get information from config file
#         lat = cfg['latitude']
#         lon = cfg['longitude']
#         return lat, lon

class getRecording_Info(Recording):

    def __init__(self, path: str, time: datetime.now, duration: float, samplerate: int):

        self.path = path
        self.time = time
        self.duration = duration
        self.sample_rate = samplerate

    def recording_info(self):
        return 

=======
# class getDeployment_Info(Deployment):
# 
#     def __init__(self,latitude: float,longitude:float):
# 
#         self.lat = latitude
#         self.lon = longitude
# 
#     def read_deployment_config(self):
# 
#         #cfg = ... get information from config file
#         lat = cfg['latitude']
#         lon = cfg['longitude']
# 
#         return lat, lon

class getRecording_Info(Recording):

    def __init__(self, path: str, time: datetime.now, duration: float, samplerate: int):

        self.path = path
        self.time = time
        self.duration = duration
        self.sample_rate = samplerate

    def recording_info(self):
        return 

>>>>>>> 5b9b0012b92c0c4ead6cabcc49bacf109c1c1d80
class PyAudioRecorder(AudioRecorder):
#class PyAudioRecorder(AudioRecorder):
    """An AudioRecorder that records a 3 second audio file."""

<<<<<<< HEAD
    def __init__(self, duration: float = DEFAULT_RECORDING_DURATION, 
                sample_rate: float = DEFAULT_SAMPLE_RATE, 
                channels: int = DEFAULT_AUDIO_CHANNELS, 
                chunk: int = DEFAULT_CHUNK_SIZE, 
                lat: float = cfg['location']['latitude'], 
                lon: float = cfg['location']['longitude']):
=======
    def __init__(self, 
                duration: float = DEFAULT_RECORDING_DURATION, 
                sample_rate: float = DEFAULT_SAMPLE_RATE, 
                channels: int = DEFAULT_AUDIO_CHANNELS, 
                chunk: int = DEFAULT_CHUNK_SIZE, 
                lat: float = cfg['location']['latitude'], 
                lon: float = cfg['location']['longitude']):
>>>>>>> 5b9b0012b92c0c4ead6cabcc49bacf109c1c1d80
        
        # Audio Duration
        self.duration = duration
       
        # Audio Microphone Parameters
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk = chunk
        
        # Device Location 
        self.lat = lat
        self.lon = lon
    
    def findAudioDevice():
        p = pyaudio.PyAudio()
        device_info = p.get_default_input_device_info()
        device_index = device_info['index']
        return device_index

    #def record_audio(self,device_index) -> Recording:
    def record(self) -> Recording:
        """Record a 3 second temporary audio file at 192KHz. Return the temporary path of the file."""       
        
        device_index = self.findAudioDevice()

        date_time = datetime.now().strftime('%Y%m%d-%H%M%S') 
   
        #Create a temporary file to record audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audiof:
            
            # Get the temporary file path from the created temporary audio file
            temp_audio_path = temp_audiof.name
            print(temp_audio_path)

            #Create an new instace of PyAudio
            p = pyaudio.PyAudio()
        
            #Open new audio stream to start recording
            stream = p.open(format=pyaudio.paInt16,
                            channels=self.channels,
                            rate=self.sample_rate,
                            input=True,
                            frames_per_buffer=self.chunk,
                            input_device_index=device_index)

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
            recording = getRecording_Info(path=temp_audio_path, time=datetime.now(), duration=self.duration, samplerate=self.sample_rate)
            return recording
