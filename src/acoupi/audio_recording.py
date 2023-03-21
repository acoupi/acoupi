"""Definition of audio recorder"""
from datetime import datetime
import tempfile
from tempfile import TemporaryFile, NamedTemporaryFile
import pyaudio
import wave 
import sounddevice
from typing import Optional, List
from dataclasses import dataclass

from acoupi_config import DEFAULT_RECORDING_DURATION, DEFAULT_SAMPLE_RATE, DEFAULT_AUDIO_CHANNELS, DEFAULT_CHUNK_SIZE, LATITUDE, LONGITUDE
from acoupi_types import Recording, AudioRecorder


# __all__ = [
    #"... all the names of the created class"
# ]

class PyAudioRecorder():
#class PyAudioRecorder(AudioRecorder):
    """An AudioRecorder that records a 3 second audio file."""

    def __init__(self, duration: float = DEFAULT_RECORDING_DURATION, sample_rate: float = DEFAULT_SAMPLE_RATE, channels: int = DEFAULT_AUDIO_CHANNELS, chunk: int = DEFAULT_CHUNK_SIZE, lat: float = LATITUDE, lon: float = LONGITUDE):
        
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

    def record_audio(self,device_index) -> Recording:
        """Record a 3 second temporary audio file at 192KHz. Return the temporary path of the file."""       
        
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

            return temp_audio_path

a = PyAudioRecorder(3,192000,1,1024,51.5381,-0.0099)
device_index = PyAudioRecorder.findAudioDevice()
PyAudioRecorder.record_audio(a,device_index)
