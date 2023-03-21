"""Definition of audio recorder"""
from datetime import datetime
import tempfile
from tempfile import TemporaryFile, NamedTemporaryFile
import pyaudio
import wave 
import sounddevice
from typing import Optional, List
from dataclasses import dataclass

from acoupi_config import DEFAULT_RECORDING_DURATION, DEFAULT_SAMPLE_RATE, DEFAULT_AUDIO_CHANNELS, DEFAULT_CHUNK_SIZE
from acoupi_types import Recording, AudioRecorder


# __all__ = [
    #"... all the names of the created class"
# ]

class PyAudioRecorder():
#class PyAudioRecorder(AudioRecorder):
    """An AudioRecorder that records a 3 second audio file."""

    def __init__(self, duration: float = DEFAULT_RECORDING_DURATION, sample_rate: float = DEFAULT_SAMPLE_RATE, channels: int = DEFAULT_AUDIO_CHANNELS, chunk: int = DEFAULT_CHUNK_SIZE):
        # Audio Duration
        self.duration = duration
       
        # Audio Microphone Parameters
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk = chunk
        
        # Device Location 
        #self.lat = lat
        #self.lon = lon
        self.lat = 51.5128
        self.lon = -0.0918

    def record_audio(self) -> Recording:
        """Record a 3 second temporary audio file at 192KHz. Return the temporary path of the file."""
       
        date_time = datetime.now().strftime('%Y%m%d-%H%M%S') 
        #audiof = tempfile.TemporaryFile(mode='w+')
        #audiof_path = tempfile.NamedTemporyFile()
        audiofile_name = ''.join('rec_%s_%s_%s' %(date_time,self.lat, self.lon) + '.wav')

        #Create interface to audio port
        p = pyaudio.PyAudio()
        
        #Start Recording
        stream = p.open(format=pyaudio.paInt16,
                        channels=self.channels,
                        rate=self.sample_rate,
                        input=True,
                        frames_per_buffer=self.chunk)

        #Initialise array to store frames
        frames = []

        #Store data in chunk of 3seconds
        for i in range(0, int(self.sample_rate/self.chunk*self.duration)):
            data = stream.read(self.chunk)
            frames.append(data)

        #Stop Recording and close the port interface
        stream.stop_stream()
        stream.close()
        p.terminate()

        # Open and Set the data of the WAV file
        audio_file = wave.open(audiofile_name, 'wb')
        print(audio_file)
        audio_file.setnchannels(self.channels)
        audio_file.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        audio_file.setframerate(self.sample_rate)

        #Write and Close the File
        audio_file.writeframes(b''.join(frames))
        audio_file.close()

        return audiofile_name

a = PyAudioRecorder(3,192000,1,1024)
PyAudioRecorder.record_audio(a)
