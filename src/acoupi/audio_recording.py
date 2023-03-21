"""Definition of audio recorder"""
from datetime import datetime
from tempfile import TemporaryFile, NamedTEmporaryFile
import pyaudio
import wave 
from typing import Optional, List
from dataclasses import dataclass

from acoupi.config import DEFAULT_RECORDING_DURATION, DEFAULT_SAMPLE_RATE, DEFAULT_AUDIO_CHANNELS, DEFAULT_CHUNK_SIZE
from acoupi.types import Recording, AudioRecorder


# __all__ = [
    #"... all the names of the created class"
# ]

class PyAudioRecorder(AudioRecorder):
    """An AudioRecorder that records a 3 second audio file."""

    def __init__(self, duration: float = DEFAULT_RECORDING_DURATION, sample_rate: float = DEFAULT_SAMPLE_RATE, channels: int = DEFAULT_AUDIO_CHANNELS, chunk: int = DEFAULT_CHUNK_SIZE):
        # Audio Duration
        self.duration = duration
       
        # Audio Microphone Parameters
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk = chunk
        
        # Device Location 
        self.lat = lat
        self.lon = lon

    def record_audio(self) -> Recording:
        """Record a 3 second temporary audio file at 192KHz. Return the temporary path of the file."""
        
        datetime = datetime.now().strftime('%Y%m%d-%H%M%S') 
        #audiof = tempfile.TemporaryFile(mode='w+')
        audiof_path = tempfile.NamedTEmporaryFile()

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

        #audiof_path.write('Some random data)')
        #audiof_path.close()
        #audiof_path.name = ''.join('rec_%s_%s_%s_%s' %(start_datetime, week_number, self.lat, self.lon) + '.wav')

        audio_file = wave.open(audiof_path, 'wb')
        audio_file.setnchannels(channels)
        audio_file.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        audio_file.setframerate(sample_rate)

        #Write and Close the File
        audio_file.writeframes(b''.join(frames))
        audio_file.close()

        return audiof_path



        