# Terminology & Definitions

__framework__: the elements constituing the acoupi software. The _acoupi_ __framework__ provides the building blocks also refered to as templates for developing a smart bioacoutics sensor. 

__system__: the set of code responsible to execute and manage an _acoupi program_ on an edge device. 

## Using acoupi

__program__: a set of instructions that dictate the behaviour of a smart bioacoutics sensor. A __program__ defines the tasks the sensor performs, how those tasks are configured, and how they are being executed. It encompasses three key elements: tasks, configuration schema, 

__pre-built program__: a _program_ that has been built with a selective set of instructions to behave in a specific manner. A __pre-built program__ is an _acoupi program_ that can be configured by users through the command line interface. Current __pre-built programs__ are listed in
[explanation: programs](explanation/programs.md/#pre-built_programs).
    
__task__: an individual unit of work carried out by a program. Each task perform specific actions, relate to other tasks in a program, and have a defined schedule. 

## Developing acoupi
__custom program__: an acoupi _program_ that does not yet exist, as opposed to an acoupi _pre-built program_. A __custom program__ refers to the steps involved in buildling a _pre-built program_. The [how-to guide: create a custom program](howtoguide/programs.md) detailed the instructions for users to follow to create a __custom program__
