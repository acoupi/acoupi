.. _advanced-guide-data:

Data
====

The **Acoupi** data layer is the most basic layer of the framework and is
responsible for defining the relevants bits of information about the
functionality of the device and the data it collects. We define data objects by
using `dataclasses <https://docs.python.org/3/library/dataclasses.html>`_ since
they are simple, lightweight, and easy to use. These data objects are used by
the other layers of the framework to perform their tasks. By providing these
data objects, we can ensure that the data handled by the other layers of the
framework is consistent and that the flow of information between the layers is
easy to understand.

.. _advanced-guide-deployments:

Deployments
-----------

A deployment object holds all the information about a specific deployment of
the Acoupi framework. This includes information about the device, the location
where the device is deployed, and the starting date. A deployment can be
created by instantiating a Deployment dataclass.

.. autoclass:: acoupi.data.Deployment
   :members:
   :undoc-members:
   :noindex:

.. _advanced-guide-recordings:

Recordings
----------

A recording object represents a single recording made by the device. It
contains information about the recording, such as the date and time when the
recording was made, the path to the audio file, and the duration of the
recording. A recording can be created by instantiating a Recording dataclass.

.. autoclass:: acoupi.data.Recording
   :members:
   :undoc-members:
   :noindex:

.. _advanced-guide-detections:

Detections
----------

A detection object represents a single detection made by some ML model. It
contains information about in which recording the detection was made, what is
the species of the animal that was detected, and the probability of the
detection. A detection can be created by instantiating a Detection dataclass.

.. autoclass:: acoupi.data.Detection
   :members:
   :undoc-members:
   :noindex:

.. _advanced-guide-messages:

Messages
--------

A message object represents a single message sent by the device. It contains
information about the message, such as the date and time when the message was
sent, the type of the message, and the content of the message. A message can
be created by instantiating a Message dataclass.

.. autoclass:: acoupi.data.Message
   :members:
   :undoc-members:
   :noindex:

Response
--------

A response object represents a single response received by the device. It
contains information about the response, such as the date and time when the
response was received, the type of the response, and the content of the
response. A response can be created by instantiating a Response dataclass.

.. autoclass:: acoupi.data.Response
   :members:
   :undoc-members:
   :noindex:
