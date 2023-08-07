Inner Workings
==============

This document serves as an overview of the execution process for user-defined
programs within the Acoupi framework on edge devices. It targets individuals
interested in modifying low-level settings or contributing to Acoupi's core
development.

The document delves into the technologies utilized to ensure the seamless
operation of user-defined programs on edge devices, providing insights into the
integration that drives Acoupi's functionality.

1. What is a Program?
---------------------

In the context of Acoupi, a program consists of a structured collection of
tasks orchestrated to establish a distinct configuration for acoustic
monitoring. Acoupi offers users the flexibility to either develop custom
programs or deploy existing ones, detailed instructions for which can be found
in the program reference.

Programs are represented as importable subclasses of
:class:`acoupi.programs.AcoupiProgram`. Any module accessible via the Python
path that contains an ``AcoupiProgram`` class is eligible for program
deployment. Users designate the desired program by providing the corresponding
module name (e.g., ``acoupi.programs.custom.test``). Acoupi facilitates class
loading using the :func:`acoupi.system.load_program` function.

Programs encompass three essential components: tasks, configuration schema, and
worker configuration. Tasks outline the operations within the program. A
configuration schema defines the program's configuration structure, and worker
configuration governs task execution.

1.1 Collection of Tasks
^^^^^^^^^^^^^^^^^^^^^^^

An Acoupi program is a set of interconnected processes that collectively
formulate a smart bioacoustic sensor. These processes are orchestrated and
synchronized utilizing the Celery framework, with individual processes referred
to as tasks.

In its essence, each task is a Python function duly registered as a
Celery task. To integrate tasks within an Acoupi program, the
:meth:`acoupi.programs.AcoupiProgram.setup` method is employed.
Within this method, users define and enroll tasks for registration
within the program using the
:meth:`acoupi.programs.AcoupiProgram.add_task` method. Behind the
scenes, the program establishes a Celery app and incorporates these
functions into the app's roster.

1.2 Program Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^

Each program within Acoupi can be accompanied by a configuration schema. This
schema serves as a blueprint, delineating the structure and data types of
configuration variables. Implementation of the schema is realized through a
:class:`pydantic.BaseModel` object.

When configuring a program for execution within the Acoupi framework, the
associated configuration schema plays a crucial role. The schema guides the
user through the definition of essential fields, facilitated by the utilization
of :func:`acoupi.system.parse_config_from_args` function. These configurations
are subsequently stored for reference.

During program execution, Acoupi leverages the stored configurations. As the
program commences, these configurations are loaded and provided to the
program's :meth:`acoupi.programs.AcoupiProgram.setup` method. This
instantiation process ensures that the program is equipped with accurate and
pertinent configurations.

1.3 Worker Configuration
^^^^^^^^^^^^^^^^^^^^^^^^

Configuring workers is a crucial part of defining an Acoupi program. Workers
handle tasks by fetching them from queues, ensuring tasks are distributed
evenly. Typically, one worker per machine is sufficient since each worker can
manage multiple tasks at once.

For simple programs, this setup works well. However, in cases like bioacoustic
sensors, some tasks can't be done simultaneously due to limited resources like
microphones. To handle this, Celery allows us to create different queues for
tasks and assign them to specific workers.

This configuration approach offers flexibility. Workers can be set to handle
tasks in a sequence within a certain queue, while other workers take care of
other tasks concurrently. This arrangement ensures tasks are executed
efficiently, even when some tasks need exclusive access to certain resources.

In Acoupi, you can utilize :class:`acoupi.programs.AcoupiWorker` objects to
configure as many workers as needed and organize them into an
:class:`acoupi.programs.WorkerConfig` object. This configuration can then be
employed when specifying the AcoupiProgram as demonstrated below:

.. code-block:: python

    MyWorkerConfig = acoupi.programs.WorkerConfig(
        workers=[acoupi.programs.AcoupiWorker(name="recording"), ...]
    )

    class MyProgram(acoupi.programs.AcoupiProgram):
        worker_config = MyWorkerConfig
        ...

This approach allows precise control over task distribution and resource
allocation within your Acoupi programs. If not specified, a single worker is
created by default.

2. How Do We Run the Program?
-----------------------------

Acoupi utilizes `Celery <https://docs.celeryq.dev/en/stable/index.html>`_ as
the framework to organize tasks and schedules. To ensure program reliability,
especially in the face of system events like reboots, we employ systemd for
managing system services.

Running a program with Celery involves designating a Celery app
(:class:`celery.Celery`). Acoupi streamlines this process by creating a
``app.py`` Python script based on user configurations. This script acts as a
bridge to expose the necessary Celery app. By using the
:func:`acoupi.system.get_celery_app` function, the script loads the
:class:`acoupi.programs.AcoupiProgram` and user configurations, then runs the
setup method to incorporate user-defined tasks into the Celery app.

Simultaneously, Acoupi generates bash scripts to launch, stop, and restart
Celery workers, complete with suitable configurations as specified in the
Acoupi program. ``systemd`` utilizes these scripts to manage Acoupi services,
ensuring reliable execution. This orchestration ensures integration of Acoupi
programs into the system.

3. Where is the Program Data Stored?
------------------------------------

Acoupi manages program setups through a dedicated directory known as
``ACOUPI_HOME``, specially designated to house all Acoupi-related files. By
default, ``ACOUPI_HOME`` is situated at the following location:

.. code-block:: bash

    $HOME/.acoupi

Whenever a new Acoupi program and its configurations are set up, the contents
within this folder adapt accordingly to the new specifications. It's important
to note that the user need not actively interact with these files, and their
existence is ideally kept hidden to prevent unintended modifications that might
disrupt system functionality.

The files in ``ACOUPI_HOME`` are created by Acoupi using templates from
the ``acoupi/templates`` folder. These templates are filled with
user-provided configurations using the `Jinja2
<https://jinja.palletsprojects.com/en/3.1.x/>`_ template engine. This
makes sure that the files in ``ACOUPI_HOME`` match the user's settings
accurately. The code generation process is handled by the
:func:`acoupi.system.setup_program` function.

The structure of the ``ACOUPI_HOME`` directory is as follows:

.. code-block:: bash

   .
   ├── app.py
   ├── bin
   │   ├── acoupi-beat.sh
   │   ├── acoupi-workers-restart.sh
   │   ├── acoupi-workers-start.sh
   │   └── acoupi-workers-stop.sh
   ├── config
   │   ├── celery.json
   │   └── program.json
   ├── log
   └── run

The ``logs`` directory stores the logs generated by Celery workers during
program execution. Meanwhile, the ``run`` directory houses the PID (process ID)
files of currently running jobs.

4. Acoupi CLI
-------------

The Acoupi Command-Line Interface (CLI) serves as the essential bridge between
users and the Acoupi backend, facilitating interaction with the acoupi system.
Utilizing the CLI simplifies the process of program setup and management.

Executing ``acoupi setup`` initiates the configuration stage. Within this
phase, users can opt for a specific program to run and provide any necessary
configurations. This process triggers the :func:`acoupi.system.setup_program`
function, which automates the creation of essential files within
``ACOUPI_HOME``, aligning them with the user's selections.

The CLI also offers ``acoupi start`` and ``acoupi stop`` commands. These
commands leverage ``systemctl`` to ensure that the associated services are
respectively enabled or disabled, thereby dictating whether the program should
run during system startup. Additionally, these commands serve to commence or
halt program execution.
