"""Process templates for Acoupi.

Acoupi offers a collection of process templates to assist in the creation of
recording, detecting, and data sending processes. While Acoupi includes a
variety of components to construct these processes, users may prefer to use
their own components. By utilizing the provided templates, users can ensure
that their custom processes integrate with Acoupi and adhere to standardized
building practices. The use of templates also allows for effortless
customization of processes.

The templates provided take the form of functions that return a function that
can be used to start a process. Each template takes a set of arguments that
are used to construct the process. The arguments are Acoupi components
of the appropriate type, such as a message store, messenger, model, etc.
Any object that implements the appropriate interface can be used as an
argument. This allows users to use out-of-the-box components or components
that they have created themselves.
"""

from acoupi.tasks.detection import generate_detection_task
from acoupi.tasks.management import generate_file_management_task
from acoupi.tasks.messaging import generate_send_data_task
from acoupi.tasks.recording import generate_recording_task

__all__ = [
    "generate_detection_task",
    "generate_recording_task",
    "generate_send_data_task",
    "generate_file_management_task",
]
