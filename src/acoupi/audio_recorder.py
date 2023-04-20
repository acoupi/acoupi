"""Implementation of AudioRecorder for acoupi.

Audio recorder is used to record audio files. Audio recorder (PyAudioRecorder) 
is implemented as class that inherit from AudioRecorder. The class should implement 
the record() method which return a temporary audio file based on the dataclass Recording.
The dataclass Recording takes a datetime.datetime object, a path from type str, 
a duration from type float, and samplerate from type float. 

The audio recorder takes arguments related to the audio device. It specifies the acoutics 
parameters of recording an audio file. These are the samplerate, the duration, the number
of audio channels, the chunk size, and the index of the audio device. The index of the audio 
device corresponds to the index of the USB port the device is connected to. The audio recorder 
return a temporary .wav file.
"""
import datetime
import tempfile
from tempfile import TemporaryFile, NamedTemporaryFile
import pyaudio
import wave 
import sounddevice
import logging
from typing import Optional, List
from dataclasses import dataclass

from acoupi_types import Recording, AudioRecorder


class PyAudioRecorder(AudioRecorder):
    """An AudioRecorder that records a 3 second audio file."""

    def __init__(self, duration: float, 
                sample_rate: float, 
                channels: int, 
                chunk: int, 
                device_index: int): 
        
        # Audio Duration
        self.duration = duration
       
        # Audio Microphone Parameters
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk = chunk
        self.device_index = device_index
        

    def record(self) -> Recording:
        """Record a 3 second temporary audio file at 192KHz. Return the temporary path of the file."""       
        
        self.datetime = datetime.datetime.now()
        
        #Create a temporary file to record audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audiof:
            
            # Get the temporary file path from the created temporary audio file
            temp_audio_path = temp_audiof.name
            
            #Create an new instace of PyAudio
            p = pyaudio.PyAudio()
            # Create new audio stream
            stream = p.open(format=pyaudio.paInt16,
                                channels=self.channels,
                                rate=self.sample_rate,
                                input=True,
                                frames_per_buffer=self.chunk,
                                input_device_index=self.device_index)
            
            # Initialise array to store audio frames 
            frames = []
            # Record audio - read the audio stream
            for i in range(0, int(self.sample_rate/self.chunk*self.duration)):
                data = stream.read(self.chunk, exception_on_overflow = False)
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