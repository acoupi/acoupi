# BatDetect2 Implementation on RPi

## Overview 
### Running BatDetect2 main.py

The implementation of BatDetect2 is based on components defined in Acoupi. To test a basic deployment of BatDetect2, various acoupi components are implemented. These consist of the following: 

1.  **RecordingScheduler**: Define how often recordings should be made. The class `IntervalScheduler` derived from RecordingScheduler uses an argument called `DEFAULT_RECORDING_INTERVAL` to set a time interval in second.
2. **RecordingCondition**: Define the specific time that recordings should be made. The class `IsInIntervals` derived from RecordingCondition uses two arguments `START_TIME` and `END_TIME` to specify the recording conditions. The conditions tell the system whether or not to record audio files. 
3. **AudioRecorder**: Define how to record audio files. The class `PyAudioRecorder` derived from AudioRecorder configures the parameters of recordings. It uses multiple arguments such as the recording duration `DEFAULT_RECORDING_DURATION` and sample rate `DEFAULT_SAMPLERATE`, and the number of audio_channels `DEFAULT_AUDIAUDIO_CHANNELS`. 
4. **Model**: Define the model that is employed to analyse audio recordings. Here, the class `BatDetect2` refers to the BatDetect2 model that detect bat calls and identify the related bat species of the audio recordings. The class BatDetect2 takes an audio recording (the output of the method `record()` from the class `PyAudioRecorder`).
5. **RecordingFilter & DetectionFilter**: Define the conditions that determine how a recording and its associated detections should be saved such as recording and detections that meet a probability threshold criteria and a specific species. For our BatDetect2 implementation, we use the classes `ThresholdRecordingFilter` and `ThresholdDetectionFilter`. Both classes require a threshold argument called `DEFAULT_THRESHOLD`. This argument is used to determine whether any detections are found above (return TRUE) or below  (return FALSE) the specifed threshold.
6. **SavingManager**: Responsible for saving the recording and the associated detections. The SavingManager contains three classes `Directories`, `SaveRecording` and `SaveDetection`. The Directories class takes two arguments: `DIR_TRUE` and `DIR_FALSE`. These arguments specify the directories in which the recordings and detections should be saved, depending on the result of the recording and detection filters. The SaveRecording and SaveDetection classes take a `DEFAULT_TIMEFORMAT` argument, which specifies the datetime format to use for the file name of the saved recording and detection. 

### Modify Arguments in BatDetect2

**Acoupi-BatDetect2** comes with a range of configurable arguments that can be used to adjust the behaviour of the acoustic monitoring system. These arguments are defined in a file called `config.py`. By changing the value of an arugment, such as `DEFAULT_THRESHOLD`, the seystem will use the new value in place of the default value. 

It is important to note that the argument names should not be changed, as doing so will require modifications to the `main.py` file. 

To modify an argument, simply locate the relevant argument `config.py`and change the value to the new desired value. For example, to adjust the threshold of the detection filters, you can change the value of `DEFAULT_THRESHOLD` to a higher or lower value. By modifying the arguments, you can fine-tune the behaviour of Acoupi-BatDetect2 to better suit your specific needs and requirements. 