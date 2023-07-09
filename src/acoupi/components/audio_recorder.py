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
import pyaudio
import wave 
import sounddevice #necessary to handle alsa error messages
from pathlib import Path 
from typing import Optional, List

from acoupi.data import Deployment, Recording 
from acoupi.components.types import AudioRecorder

TMP_PATH = Path("/run/shm/")

class PyAudioRecorder(AudioRecorder):
    """An AudioRecorder that records a 3 second audio file."""

    def __init__(self, 
                duration: float, 
                samplerate: float, 
                audio_channels: int, 
                chunk: int, 
                device_index: int): 
        
        # Audio Duration
        self.duration = duration
       
        # Audio Microphone Parameters
        self.samplerate = samplerate
        self.audio_channels = audio_channels
        self.chunk = chunk

        if device_index is None:
            # Get the index of the audio device
            self.device_index = self.get_device_index()

        self.device_index = device_index


    def get_device_index(self) -> int:
        """Get the index of the audio device."""
        # Create an instance of PyAudio
        p = pyaudio.PyAudio()

        # Get the number of audio devices
        num_devices = p.get_device_count()

        # Loop through the audio devices
        for i in range(num_devices):
            # Get the audio device info
            device_info = p.get_device_info_by_index(i)

            # Check if the audio device is an input device
            if int(device_info["maxInputChannels"]) <= 0:
                continue

            # Get the index of the USB audio device
            device_index = int(device_info["index"])
            return device_index

        raise ValueError("No USB audio device found")


    def record(self, deployment: Deployment) -> Recording:

        """Record a 3 second temporary audio file. Return the temporary path of the file."""       
        
        #device_index = self.findAudioDevice()
        self.datetime = datetime.datetime.now()

        # Specified the desired path for temporary file - Saved in RAM
        temp_path = TMP_PATH / f'{self.datetime.strftime("%Y%m%d_%H%M%S")}.wav'
        
        #Create a temporary file to record audio
        with open(temp_path, 'wb') as temp_audiof:
            
            temp_audio_path = temp_audiof.name
            print(f'Temporary Audio File Path: {temp_audio_path}')
            print("")

            #Create an new instace of PyAudio
            p = pyaudio.PyAudio()

            #Open new audio stream to start recording
            stream = p.open(format=pyaudio.paInt16,
                            channels=self.audio_channels,
                            rate=self.samplerate,
                            input=True,
                            frames_per_buffer=self.chunk,
                            input_device_index=self.device_index)


            #Initialise array to store audio frames
            frames = []
            for i in range(0, int(self.samplerate/self.chunk*self.duration)):
                data = stream.read(self.chunk, exception_on_overflow = False)
                frames.append(data)

            #Stop Recording and close the port interface
            stream.stop_stream()
            stream.close()
            p.terminate()

            #Create a WAV file to write the audio data
            with wave.open(temp_audio_path, 'wb') as temp_audio_file:
                temp_audio_file.setnchannels(self.audio_channels)
                temp_audio_file.setsampwidth(p.get_sample_size(pyaudio.paInt16))
                temp_audio_file.setframerate(self.samplerate)

                # Write the audio data to the temporary file
                temp_audio_file.writeframes(b''.join(frames))    
                temp_audio_file.close()

                # Create a Recording object and return it
                return Recording(
                    path=Path(temp_audio_path), 
                    datetime=self.datetime, 
                    duration=self.duration, 
                    samplerate=self.samplerate,
                    deployment=deployment)
                
