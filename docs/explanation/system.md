# System

This section provides an in-depth exploration of _acoupi_'s **System** module.
The **System** is responsible for ensuring the accurate execution of user-defined programs.

??? info "Intended Audience"

    This section is geared towards individuals interested in understanding or modifying low-level settings or contributing to _acoupi_'s core development.

??? warning "Pre-requisites"

    Before proceeding, please ensure you have familiarized yourself with the following sections of the Explanation:

    * [**Data Schema**](data_schema.md)
    * [**Components**](components.md)
    * [**Tasks**](tasks.md)
    * [**Programs**](programs.md)

## Overview

As outlined in the architecture section, the _acoupi_ system can be conceptually divided into three interconnected parts:

- **CLI**: This provides a user interface for selecting and configuring the desired program, deploying the device with the setup program, and checking its status.

- **Management Layer**: This layer manages program and configuration files, ensuring proper setup for program execution, and maintains logs and tracks the program's state.

- **Orchestration**: This part handles the robust execution of the program.

In the following sections, we'll elaborate on how these parts work together to enable users to run their programs.

<figure markdown="span">
    ![Figure 1: Overview of the inner-working of acoupi](../img/acoupi_celery_app.png){ width="100%" }
    <figcaption><b>Overview of the inner-working of an acoupi application.</b> An acoupi program is executed using the [Celery](https://docs.celeryq.dev/en/stable/getting-started/introduction.html) framework. Celery works in the background to organise the execution of acoupi tasks using queues and workers.
</figure>

## 1. CLI

The _acoupi_ CLI serves as the primary interface between the users and _acoupi_ systems.
It empowers users to perform the following key actions:

- **Program Selection**: Users can define the desired program and its associated configurations.
- **Configuration Management**: The CLI allows users to view, modify, and fine-tune configurations.
- **Configuration Validation**: A crucial step before deployment, the CLI enables users to verify the correctness of their current configurations.
- **Device Deployment**: Users can initiate device deployment with the specified program and configurations.
- **Status Monitoring**: The CLI provides a means to check the current status of _acoupi_.
- **Deployment Termination**: Users can gracefully stop the ongoing deployment.

The _acoupi_ CLI offers step-by-step configuration wizards and provides valuable feedback on user inputs.
For a comprehensive list of available commands and their usage instructions, refer to the documentation for the [`acoupi.cli`](../reference/cli.md) module.
The CLI is built using the [**Click**](https://click.palletsprojects.com/en/8.1.x/) framework.

## 2. Management

The _acoupi_ **System** manages the system setup to align with user needs.
This involves tracking the selected program, configurations, and deployment details.
Furthermore, the **System** actively maintains synchronization of the files necessary for program execution.
To facilitate observability and error identification, _acoupi_ maintains comprehensive logs.

### Home Directory

_acoupi_ centralizes all essential data and files within the `ACOUPI_HOME` directory.
By default, this directory is set to `$HOME/.acoupi`, but users can customize its location by modifying the `ACOUPI_HOME` environment variable.

!!! warning

    It's important to note that the user need not actively interact with these files, and their existence is ideally kept hidden to prevent unintended modifications that might disrupt system functionality.

Here's a concise overview of the files and structure within the _acoupi_ home directory:

```bash
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
│   ├── default.log
│   └── recording.log
└── run
    ├── celery-beat.pid
    └── celery-worker-1.pid
```

### Tracking Program and Configurations

When the user specifies the program to run and/or modifies configurations, _acoupi_ updates the following files:

- `$ACOUPI_HOME/app.py`: This Python script loads and exposes the currently selected program along with its configurations to Celery, effectively instructing its execution.
- `$ACOUPI_HOME/config/program.json`: This JSON file stores the user-provided configurations for the program execution.

### Execution Files

_acoupi_ generates scripts within the `$ACOUPI_HOME/bin` folder to manage Celery operations (start, stop, restart, and schedule tasks).
These scripts direct Celery to utilize the `$ACOUPI/app.py` file for the definition of the Celery app, which encapsulates the _acoupi_ program to be executed.

### Logs and Status

The `logs` directory serves as a repository for logs generated by Celery workers during program execution.
Concurrently, the `run` directory stores the PID (process ID) files of actively running jobs, aiding in process management and monitoring.

### Code Generation

_acoupi_ employs templates located in the `acoupi/templates` folder to dynamically generate the files within `ACOUPI_HOME`.
These templates are populated with user-provided configurations using the [Jinja2](https://jinja.palletsprojects.com/en/3.1.x/) template engine.
This ensures that the generated files within `ACOUPI_HOME` accurately reflect the user's specific settings.

## 3. Orchestration

Upon deployment initiation, _acoupi_ invokes the necessary steps to prepare the device for program execution.
It utilizes [Celery](https://docs.celeryq.dev/en/stable/index.html) as the framework to execute and schedule tasks.
_acoupi_ initializes Celery workers and starts executing the Celery app defined within the current _acoupi_ program.
Simultaneously, [systemd](https://systemd.io/) is employed to install _acoupi_ as a system service, ensuring automatic restarts in case of failures or system reboots.

### Celery App

A crucial aspect of running a program with Celery is designating a [Celery app][celery.Celery].
_acoupi_ does this by dynamically generating an `app.py` Python script based on user configurations.
This script serves as a bridge, exposing the required Celery app.

The [acoupi.system.get_celery_app()][acoupi.system.get_celery_app] function loads the [AcoupiProgram][acoupi.programs.AcoupiProgram] and user configurations, then executes the setup method to integrate user-defined tasks into the Celery app.
More generally, the functions used to manage celery are all located in the [`acoupi.system.celery`][acoupi.system.celery] module.

### Workers

Celery workers execute tasks by fetching them from queues, ensuring balanced workload distribution.
Typically, one worker per machine suffices as each worker can handle multiple tasks concurrently.
However, in bioacoustics sensor systems, certain tasks might necessitate exclusive hardware resources, like microphone inputs, precluding simultaneous execution.

To address this, Celery allows the creation of multiple queues, enabling specific workers to fetch tasks from designated queues.
This approach grants flexibility by permitting sequential task processing within a particular queue (concurrency of 1), while other workers handle tasks concurrently in other queues.
The [AcoupiWorker][acoupi.programs.AcoupiWorker] class allows for configuring multiple workers and organizing them into an [WorkerConfig][acoupi.programs.WorkerConfig] object.
This configuration is then utilized when creating the [AcoupiProgram][acoupi.programs.AcoupiProgram].

!!! Example

    ```python

        from acoupi.programs import WorkerConfig, AcoupiWorker, AcoupiProgram

        worker_config = WorkerConfig(
            workers=[
                AcoupiWorker(
                    name="recording",
                    queues=["recording"],
                    concurrency=1,
                ),
                AcoupiWorker(
                    name="default",
                    queues=["celery"],
                ),
            ],
        )

        class MyProgram(AcoupiProgram):
            worker_config = worker_config

            ...

    ```

This approach allows precise control over task distribution and resource allocation within your **acoupi** programs.
If not specified, a single worker is created by default.

The program configuration is used to generate the `acoupi-workers-{stop|start|restart}.sh` files.
For more info look at the [`acoupi.system.scripts`][acoupi.system.scripts] module on how they are generated.

### Systemd Units

_acoupi_ generates service units that are installed as user units.
When deployment starts, the unit is enabled and initiated.
Consequently, systemd manages the initialization, restart, and shutdown of Celery workers and their execution, ensuring robust integration of _acoupi_ programs into the system.

In particular, acoupi uses the [`acoupi.system.services`][acoupi.system.services] module to generate, install and manage the systemd unit files.
