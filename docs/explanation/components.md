# Components (acoupi framework)

The **components** are the building blocks of all **acoupi** functionality.
Each component is designed to perform a specific action, such as recording audio, processing recordings, or sending messages to a remote server.
They have a single responsibility and are designed to be reusable and modular.

The set of components available in the acoupi software package was chosen to reflect the diversity of configurations across bioacousticsurveys.
When researchers plan a bioacoustic survey, they are confronted with a series of questions related to the workflow of their bioacousticsensors.
Examples of questions assigned to acoupi components are:

- [**RecordingConditions**](#recording_conditions): “At what time of the day should audio recordings be collected?”
- [**RecordingSchedulers**](#recording_schedulers): “How long should the audio recordings last?”
- [**AudioRecorder**](#audio_recorder): “What type of microphone should be used?”, “At which frequency should the recordings be recorded?”
- [**Models**](#model): “How will audio files be processed?”, “What kind of automated bioacousticclassifiers can be used?”
- [**ModelOutputCleaners**](#model_output_cleaners): “Which information should be kept? ”, “What detection threshold should be used?”
- [**Messengers**](#messengers): "What type of network connectivity is available: WiFi, Ethernet, LoRa, Satellite?”, “What messaging protocol is used: HTTP, MQTT?”, “When should connectivity be enabled: one an hour/day/week, every positive detection?”
- [**Saving Managers**](#recording_saving_managers): “Should all the audio recordings be saved?”
- [**Saving Filters**](#recording_saving_filters): “What filters should be used for saving audio recordings: time based, detections based, species based?
- [**Store**](#stores): “Where should the audio recordings and audio classifications results be saved?” “How should the recordings, classifications results be saved?”
- [**Summariser**](#summarisers): “Should a summary of the deployment, recordings, detections be created?”

## Overview Components

??? Tip "Building you own components"

    Please check the [_How To Guides: Components Section_](../howtoguide/components.md) for a step-by-step guide about building your own component, if none of the acoupi pre-built component suit your needs.

The components mentioned aboved are abstract components (i.e., Python classes).
They are examples of the abstraction concept.
These abstract component classes are templates that are used by the implemented components (i.e, subclasses) of a deployed acoupi program.
The implemented components are called “subclasses”, as they inherit from the abstract component classes.

Below we provide details about each of the abstract components and mentioned the currently available pre-built subclasses for each.

#### Recording Conditions

The [types.RecordingConditions][acoupi.components.types.RecordingCondition] component is in charge of verifying if a certain condition for recording is met, such as checking whether or not it is time for the system to record audio files.
Acoupi comes with the class `IsInIntervals` configured.
The class implement the `should_record()` method that takes datetime.datetime objects `start_recording` and `end_recording` and returns a boolean indicating if a recording should be made at that time.

#### Recording Schedulers

The [types.RecordingSchedulers][acoupi.components.types.RecordingScheduler] component defines how often recordings should be made.
This is useful for example if you want to record at a constant interval, or if you want to record at a variable interval, such as every 10 minutes during the day and every 30 minutes at night.
The Recording Schedulers implement the `time_until_next_recording()` method, which returns the time in seconds until the next recording should be made.

#### Audio Recorder

The [types.AudioRecorder][acoupi.components.types.AudioRecorder] component defines how to record audio files.
The AudioRecorde' subclass called `PyAudioRecorder` configures the parameters of recordings.
It uses multiple arguments such as the recording duration `audio_duration`, the sample rate `samplerate`, the number of audio_channels `audio_channels`, the device index `device_index` and the audio chunk size `chunksize`.
The class and subclass implement the `record()` method.

#### Model

The [types.Model][acoupi.components.types.Model] component is in charge of processing a recording and generating predictions.
This includes running machine learning models to detect specific sounds or patterns in the audio.
Define the model that is employed to analyse audio recordings.
Here, the class name refers to the bioacousticmodel name that detect, classify or identify related species in audio recordings.
Acoupi comes with two pre-built models [**BatDetect2**](https://github.com/macaodha/batdetect2) for UK Bat species detection and [**BirdNET**](https://github.com/kahst/BirdNET-Lite) for bird species classification.
The `Model` class should implement the `run()` method that takes the path of the audio recording files.

#### Model Output Cleaners

The [types.ModelOutputCleaners][acoupi.components.types.ModelOutputCleaner] component defines how a recording and its associated detections should be handled.
The subclass `ThresholdDetectionFilter` takes as argument a threshold value to determine how to clean the raw detections.
The detections below the threshold are deleted, the detections above the threshold are kept.

#### Recording Saving Filters

The [types.RecordingSavingFilters][acoupi.components.types.RecordingSavingFilter] component defines conditions for saving the audio recordings.
The class implements many subclasses such as `BeforeDawnDusk`, `AfterDawnDusk`, `SaveIfInInterval`, `FrequencySchedule`, `FocusSpeciesRecordingFilter`.
The SavingFilters class is optional.
If not defined, audio files by default will not be saved.

#### Recording Saving Managers

The [types.RecordingSavingManagers][acoupi.components.types.RecordingSavingManager] component defines where and how the audio recordings should be saved such as saving recordings into a specific format and at a specific location (i.e., RPi SDcard, external harddrive, folder XX/YY).
The class implements two subclasses `IDFileManager` and `DateFileManager`.

#### Messengers

The [types.Messengers][acoupi.components.types.Messenger] component defines how to send detections (i.e., clean model outputs) to a remote server.
The class implements two subclasses `MQTTMessenger` and `HTTPMessenger`.

#### Stores

The [types.Stores][acoupi.components.types.Store] component is in charge of storing the information ofwhat recordings and detections have been made.
This includes storing metadata about the recordings and detections, such as the date and time of the recording, and the type of animal or sound detected.
The class implements the subclass `SqliteStore`.

#### Message Stores

The [types.MessageStores][acoupi.components.types.MessageStore] component is charge of storing information about which messages have been successfully sent or are missing.
This allows retrying sending messages if they fail to send, or that can log the status of messages for later analysis.

By combining these categories of components, it is possible to create complex programs that can perform a wide variety of monitoring tasks.
Each component can be configured to operate in a specific way, and can be combined with other components to create customised functionality.

#### Summarisers

The [types.Summariser][acoupi.components.types.Summariser] component is responsible for summarising information related to the deployment of acoupi, its recordings and detections.
The class implement two subclasses `StatisticsDetectionsSummariser` and `ThresholdsDetectionsSummariser`.
