## BatDetect2 Implementation on RPi

### Overview 

**Running BatDetect2 main.py**

The implementation of BatDetect2 is based on components defined in Acoupi. To test a basic deployment of BatDetect2, various acoupi components are implemented. These consist of the following: 

1.  **RecordingScheduler**: Define how often recordings should be made. The class `IntervalScheduler` derived from RecordingScheduler uses an argument called `DEFAULT_RECORDING_INTERVAL` to set a time interval in second.
2. **RecordingCondition**: Define the specific time that recordings should be made. The class `IsInIntervals` derived from RecordingCondition uses two arguments `START_TIME` and `END_TIME` to specify the recording conditions. The conditions tell the system whether or not to record audio files. 
3. **AudioRecorder**: Define how to record audio files. The class `PyAudioRecorder` derived from AudioRecorder configures the parameters of recordings. It uses multiple arguments such as the recording duration `DEFAULT_RECORDING_DURATION` and sample rate `DEFAULT_SAMPLE_RATE`, and the number of audio channels `DEFAULT_AUDIO_CHANNELS`. 
4. **Model**: Define the model that is employed to analyse audio recordings. Here, the class `BatDetect2` refers to the BatDetect2 model that detect bat calls and identify the related bat species of the audio recordings. The class BatDetect2 takes an audio recording (the output of the method `record()` from the class `PyAudioRecorder`).




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