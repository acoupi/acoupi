# Components

Components are the building blocks of all **acoupi** functionality. Each
component is designed to perform a specific task, such as recording audio,
processing recordings, or sending messages to a remote server. They have a
single responsibility and are designed to be reusable and modular pieces.

# Component Types

We have subdivided the components into several categories based on our analysis
of what a bioacoustic sensor might need. These categories are:

[**Recording Conditions**][acoupi.components.recording_conditions]: In charge of
verifying if a certain condition for recording is met, such as checking whether
or not it is time for the system to record audio files. Acoupi comes with the
class `IsInIntervals` configured. The class implement the `should_record()`
method that takes datetime.datetime objects `start_recording` and
`end_recording` and returns a boolean indicating if a recording should be made
at that time.

[**Recording Schedulers**][acoupi.components.recording_schedulers]: Define how
often recordings should be made. This is useful for example if you want to
record at a constant interval, or if you want to record at a variable interval,
such as every 10 minutes during the day and every 30 minutes at night. The
Recording Schedulers implement the `time_until_next_recording()` method, which
returns the time in seconds until the next recording should be made.

[**AudioRecorders**][acoupi.components.audio_recorder]: Define how to record
audio files. The class `PyAudioRecorder` derived from AudioRecorder configures
the parameters of recordings. It uses multiple arguments such as the recording
duration `audio_duration`, the sample rate `samplerate`, the number of
audio_channels `audio_channels`, the device index `device_index` and the audio
chunk size `chunksize`. The class should implement the `record()` method.

[**Models**][acoupi.components.models]: In charge of processing a recording and
generating predictions. This includes running machine learning models to detect
specific sounds or patterns in the audio. Define the model that is employed to
analyse audio recordings. Here, the class name refers to the bioacoustics model
name that detect, classify or identify related species in audio recordings.
Acoupi comes with two pre-built models
[`BatDetect2`](https://github.com/macaodha/batdetect2) for UK Bat species
detection and [`BirdNET`](https://github.com/kahst/BirdNET-Lite) for bird
species classification. The `Model` class should implement the `run()` method
that takes the path of the audio recording files.

**[ProcessingFilters][acoupi.components.processing_filters] &
[OutputCleaners][acoupi.components.output_cleaners]**: Define the conditions
that determine how a recording and its associated detections should be saved
such as recording and detections that meet a probability threshold criteria and
a specific species. We implemented the classes `ThresholdRecordingFilter` and
`ThresholdDetectionFilter`. Both classes require a threshold argument called
`threshold`. This argument is used to determine whether any detections are found
above (return TRUE) or below (return FALSE) the specifed threshold.

[**SavingFilters**][acoupi.components.saving_filters]: Responsible for saving
the audio recordings. The SavingFilters class is optional. It allows a user to
save audio recording files on a SD Card. The SavingFilters implemented many
subclasses to allow for specific use cases. Examples of classes are
`Before_DawnDusk`and `After_DawnDusk`, `Detection_Threshold`,
`FrequencySchedule`, and `Start_Time` and `End_Time`. The SaveRecordingFilters
classes take a `TIMEFORMAT` argument, which specifies the datetime format to use
for the file name.

[**Messengers**][acoupi.components.messengers]: In charge of sending information
to a remote server.

[**Stores**][acoupi.components.stores]: In charge of storing the information of
what recordings and detections have been made. This includes storing metadata
about the recordings and detections, such as the date and time of the recording,
and the type of animal or sound detected.

[**Message Stores**][acoupi.components.message_stores]: In charge of storing
information about which messages have been successfully sent or are missing.
This allows retrying sending messages if they fail to send, or that can log the
status of messages for later analysis.

By combining these categories of components, it is possible to create complex
programs that can perform a wide variety of monitoring tasks. Each component can
be configured to operate in a specific way, and can be combined with other
components to create customized functionality.

# Custom Components

To create a custom component that will play nicely with Acoupi it is best to
follow the following guidelines:

1. If the component you wish to implement can be categorized as one of the
   categories described above, then it should inherit from the corresponding
   base class and try to stick with the suggested interface. For example, if you
   are implementing a component that will be in charge of recording audio, then
   it should inherit from the `AudioRecorder` class.

2. If the component you wish to implement does not fit into any of the the
   mentioned categories, then it should try to have a simple interface that uses
   the data schema defined in `data_schema`. This will allow the component to be
   easily combined with other components defined in Acoupi.

3. If you wish to share your component with the Acoupi community, then make sure
   you checkout the `acoupi-contributing` section!
