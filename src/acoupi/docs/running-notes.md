## BatDetect2 Implementation on RPi

### Step 1 - Recording Audio Files

**Application**

Iniating an audio recorder to record audio file using the PyAudioRecorder class. The PyAudioRecorder class implements the record() method. The PyAudioRecorder takes arguments to configure the parameters of an audio recording These are samplerate, duration, number of audio channels, size of chunk, and index of audio device. 

In the case of BatDetect2 and using a Dodotronic microphone the parameters are set to the following:
- duration: 3 (in seconds)
- samplerate: 192000 (in Hz)
- channels: 1
- chunk: 2048

These parameters can be modify in the `config.py` script. Note that the index of the audio_device is set by the installation script `setup_microphone.sh`.

**Theory**

The PyAudioRecorder class derives from the AudioRecorder abstract class, which is defined in the types.py script. The types.py script aims to describe the building blocks for an acoustic classification on raspberrypi "acoupi" appplication to run.

# Step 2 - Processing Audio Files



# Step 3 - Saving Model Outputs