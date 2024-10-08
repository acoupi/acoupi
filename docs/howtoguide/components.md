# Create Custom Components

_acoupi_ comes with a series of pre-defined [**components**](../reference/components.md) that allow the customisation of _acoupi_ [**tasks**](../reference/tasks.md), such as recording audio at specific time of the day or sending messages to a remote server using specific messaging protocols (e.g., MQTT, HTTP).

For use cases requiring more specialised behaviour, new custom components can be created.
There are two different processes to create new components.

1. Case 1: Create components from pre-built templates
2. Case 2: Create components from scratch

??? Info "Component Inheritance?"

      Pre-built templates are **abstract components** inherited from types. When creating a new component, it is important to understand the difference
      between creating a new abstract class with an associated subclass or creating a new subclass inheriting from pre-built abstract classes. See _Example Sections_ below for examples of pre-built abstract classes and subclass.

## 1. Create components from pre-built templates

Pre-built templates are the abstract component classes defined in _acoupi_ module [**components/types.py**](../reference/components.md).
These templates defined the functions of an _acoupi_'s component, yet requires implementation to be integrated into program tasks.

!!! Example "Example of abstract components (types.py)."

      ```python

      from abc import ABC, abstractmethod

      from acoupi import data

      class Component(ABC):
            """An abstract component."""

            @abstractmethod
            def component_method(self, input) -> output


      class RecordingCondition(ABC):
            """A component to decide if a recording should be made."""

            @abstractmethod
            def should_record(self) -> bool


      class Model(ABC):
            """A component to run a model on a recording and ouput predictions."""

            @abstractmethod
            def run(self, data.Recording) -> data.ModelOutput
      ```

Is there an abstract component that would suit a newly created component subclass? If so, the new component subclass should inherit from the abstract component.
An example of a new component subclass could be one that specifies when recordings should occur.

!!! Example "Create new subclass inheriting from types.RecordingConditions."

      ```python
      import datetime

      from astral import LocationInfo
      from astral.sun import sun

      from acoupi import data
      from acoupi.components import types

      class DawnTimeInterval(types.RecordingConditions):
            """A RecordingCondition that records within a time interval before and after dawn."""

            duration: float
            "The duration of time (in minutes) where recording should occur."

            timezone: datetime.tzinfo
            """The timezone of the deployed device to get the dawn time."""

            time: datetime.datetime
            """The current time. Check if it falls within the interval."""

            def __init__(self, duration, timezone, time):
                  self.duration = duration
                  self.timezone = timezone
                  self.time = time

            def should_record(self) -> bool
                  """Determine if a recording should be made."""

                  sun_info = sun(
                        LocationInfo(str(self.timezone)).observer,
                        date=self.time.astimezone(self.timezone),
                        tzinfo=self.timezone,
                  )

                  dawntime = sun_info["dawn"]

                  start_dawninterval = dawntime - datetime.timedelta(minutes=self.duration)
                  end_dawninterval = dawntime + datetime.timedelta(minutes=self.duration)

                  return start_dawninterval.time() <= self.time.time() <= end_dawninterval.time()
      ```

## 2. Create components from scratch

If the component you wish to implement does not fit into any of the pre-built abstract classes, then you should try to define a simple template as described in the example of abstract components with input and output parameters that uses the data objects such as the ones defined in [`data_schema`](../reference/data.md).
