.. _advanced-guide-components:

Components
==========

Components are the building blocks of all Acoupi functionality. Each
component is designed to perform a specific task, such as recording audio,
processing recordings, or sending messages to a remote server. They have a
single responsibility and are designed to be reusable and modular pieces.

Component Types
---------------

We have subdivided the components into several categories based on our analysis
of what a bioacoustic sensor might need. These categories are:

* :ref:`Recording Conditions<recording_conditions>`: In charge of verifying if
  a certain condition for recording is met, such as checking if the ambient
  noise is below a certain level.

* :ref:`Audio Recorders<audio_recorders>`: In charge of handling the
  microphones and recording audio.

* :ref:`Models<models>`: In charge of processing a recording and generating
  predictions. This includes running machine learning models to detect specific
  sounds or patterns in the audio.

* :ref:`File Managers<file_managers>`: In charge of storing and managing audio
  files in the filesystem. This includes organizing files by date or other
  criteria, and deleting files.

* :ref:`Stores<stores>`: In charge of storing the information of what
  recordings and detections have been made. This includes storing metadata
  about the recordings and detections, such as the date and time of the
  recording, and the type of animal or sound detected.

* :ref:`Processing Filters<processing_filters>`: In charge of determining
  whether a recording should be processed by models or not. This includes
  filters based on criteria such as a simple threshold on the signal-to-noise
  ratio of the recording, or some other very computationally cheap criteria
  such as a amplitude threshold on an specific frequency band.

* :ref:`Detection Filters<detection_filters>`: In charge of specifying which
  detections are relevant and should be stored. This includes filters based on
  criteria such as the confidence level of the detection or the type of animal
  or sound detected.

* :ref:`Recording Filters<recording_filters>`: In charge of specifying which
  recordings should be deleted or kept in the filesystem based on the
  detections. This includes filters based on criteria such as the number of
  detections made, the type of animal or sound detected, or the time of day.

* :ref:`Messengers<messengers>`: In charge of sending information to a remote
  server.

* :ref:`Message Stores<message_stores>`: In charge of storing information about
  which messages have been successfully sent or are missing. This allows
  retrying sending messages if they fail to send, or that can log the status of
  messages for later analysis.

By combining these categories of components, it is possible to create complex
programs that can perform a wide variety of monitoring tasks. Each component
can be configured to operate in a specific way, and can be combined with other
components to create customized functionality.

.. _advanced-guide-component-library:

Component Library
-----------------

The following sections describe the components that are currently available in
Acoupi.

.. _recording_conditions:

Recording Conditions
~~~~~~~~~~~~~~~~~~~~

.. _audio_recorders:

Audio Recorders
~~~~~~~~~~~~~~~

.. _models:

Models
~~~~~~

.. _file_managers:

File Managers
~~~~~~~~~~~~~

.. _stores:

Stores
~~~~~~

.. _processing_filters:

Processing Filters
~~~~~~~~~~~~~~~~~~

.. _detection_filters:

Detection Filters
~~~~~~~~~~~~~~~~~

.. _recording_filters:

Recording Filters
~~~~~~~~~~~~~~~~~

.. _messengers:

Messengers
~~~~~~~~~~

.. _message_stores:

Message Stores
~~~~~~~~~~~~~~


.. _advanced-guide-custom-components:

Custom Components
-----------------
