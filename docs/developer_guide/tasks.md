# Tasks

An **acoupi** program is a set of interconnected processes that collectively formulate a smart bioacoustic sensor. These processes are orchestrated and synchronized utilizing the Celery framework, with individual processes referred to as tasks.

In its essence, each task is a Python function duly registered as a Celery task. To integrate tasks within an Acoupi program, the [`acoupi.system.AcoupiProgram.setup`](/src/acoupi/system/programs/base.py) method is employed. Within this method, users define and enroll tasks for registration within the program using the [`acoupi.system.AcoupiProgram.add_task`](/src/acoupi/system/programs/base.py) method. Behind the scenes, the program establishes a Celery app and incorporates these functions into the app's roster.
