# System (acoupi application)

The following section describes the inner-workings of an **acoupi** application.
It provides an overview of the system suppporting the execution of an acoupi program.
These explaination should interest individuals that are keen to modify low-level settings or contribute to acoupi's core development.

!!! Important

    Please ensure you have read the [**Data Schema**](data_schema.md), [**Components**](components.md), [**Tasks**](tasks.md), and [**Programs**](programs.md) sections of the _Explanation_ before diving further.

<figure markdown="span">
    ![Figure 1: Overview of the inner-working of acoupi](../img/acoupi_celery_app.png){ width="100%" }
    <figcaption><b>Overview of the inner-working of an acoupi application.</b> An acoupi program is executed using the [Celery](https://docs.celeryq.dev/en/stable/getting-started/introduction.html) framework. Celery works in the background to organise the execution of acoupi tasks using queues and workers.
</figure>

## 1. Workers

Workers execute tasks by fetching them from queues, ensuring an even distribution of workload.
As each worker can handle multiple tasks concurrently, one worker per machine is often enough.

However, in cases like bioacoustics sensor systems, certain tasks may require exclusiive hardware resources, such as microphone inputs, preventing simultaneous execution.
To address this, Celery allows the creation of multiple queues, enabling specific workers to fetch tasks in designated queues.

This approach offers flexibility by allowing workers to process tasks sequentially within a certain queue (i.e., with a concurrency of 1), while other workers handle other tasks concurrently.
This arrangement ensures efficient task execution, even when certain resources need to be dedicated to specific tasks.

The class [`acoupi.programs.AcoupiWorker`][acoupi.programs.core.workers.AcoupiWorker] allow to configure as many workers as needed and organize them into an [`acoupi.programs.WorkerConfig`][acoupi.programs.core.workers.WorkerConfig] object.
This configuration can then be employed when specifying the AcoupiProgram as demonstrated below:

!!! Example

    ```python

        from acoupi.programs.core import WorkerConfig, AcoupiWorker

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

    ```

This approach allows precise control over task distribution and resource allocation within your **acoupi** programs.
If not specified, a single worker is created by default.

## 2. Running Programs

**acoupi** uses [**Celery**](https://docs.celeryq.dev/en/stable/index.html) as the framework to organise and schedule tasks.
To ensure program reliability, especially in the face of system events like reboots, we employ systemd for managing system services.

Running a program with Celery involves designating a Celery app [`celery.Celery`](https://docs.celeryq.dev/en/stable/reference/celery.html#celery.Celery).
**acoupi** streamlines this process by creating an `app.py` Python script based on user configurations.
This script acts as a bridge to expose the necessary Celery app.
By using the [`acoupi.system.get_celery_app()`][acoupi.system.get_celery_app] function, the script loads the [`acoupi.programs.AcoupiProgram`][acoupi.programs.AcoupiProgram] and user configurations, then runs the setup method to incorporate user-defined tasks into the Celery app.

Simultaneously, Acoupi generates bash scripts to start, stop, and restart Celery workers, complete with suitable configurations as specified in the **acoupi** program.
`systemd` uses these scripts to manage **acoupi** services, ensuring reliable execution.
This orchestration ensures integration of **acoupi** programs into the system.

## 3. Where is the Program Data Stored?

Acoupi manages program setups through a dedicated directory known as `ACOUPI_HOME`, specially designated to house all Acoupi-related files.
By default, `ACOUPI_HOME` is situated at the following location:

```bash
$HOME/.acoupi
```

Whenever a new **acoupi** program and its configurations are set up, the contents within `ACOUPI_HOME` adapt accordingly to the new specifications.
It's important to note that the user need not actively interact with these files, and their existence is ideally kept hidden to prevent unintended modifications that might disrupt system functionality.

The files in `ACOUPI_HOME` are created by **acoupi** using templates from the `acoupi/templates` folder.
These templates are filled with user-provided configurations using the [**Jinja2**](https://jinja.palletsprojects.com/en/3.1.x/) template engine.
This makes sure that the files in `ACOUPI_HOME` match the user's settings accurately.
The code generation process is handled by the [`acoupi.system.setup_program()`][acoupi.system.setup_program] function.

The `ACOUPI_HOME` directory has the following structure:

!!! Example

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
    └── run
    ```

The `logs` directory stores the logs generated by Celery workers during program execution.
Meanwhile, the `run` directory houses the PID (process ID) files of currently running jobs.
