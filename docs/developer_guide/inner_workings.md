# How it works?


This document serves as an overview of the execution process for user-defined programs within the **acoupi** framework on edge devices. It targets individuals interested in modifying low-level settings or contributing to Acoupi's core development.

The document delves into the technologies utilized to ensure the seamless operation of user-defined programs providing insights into the integration that drives Acoupi's functionality.

Please ensure you have read the [**Data Schema**](/docs/developer_guide/data_schema.md), [**Components**](/docs/developer_guide/components.md), [**Tasks**](/docs/developer_guide/tasks.md), and [**Programs**](/docs/developer_guide/programs.md) sections before diving further. Each of the 4 sections describe the core layers of the **acoupi** framework. 


## 1. Workers

Workers handle tasks by fetching them from queues, ensuring tasks are distributed evenly. Typically, one worker per machine is sufficient since each worker can manage multiple tasks at once.

For simple programs, this setup works well. However, in cases like bioacoustic
sensors, some tasks can't be done simultaneously due to the limitation of the hardware resources such as microphones inputs. To handle this, Celery allows to create different queues for tasks and assign them to specific workers.

This configuration approach offers flexibility. Workers can be set to handle
tasks in a sequence within a certain queue, while other workers take care of
other tasks concurrently. This arrangement ensures tasks are executed
efficiently, even when some tasks need exclusive access to certain resources.

The class [`acoupi.programs.AcoupiWorker`](/src/acoupi/programs/workers.py)
allow to configure as many workers as needed and organize them into an
[`acoupi.programs.AcoupiWorker`](/src/acoupi/programs/workers.py) object. This configuration can then be employed when specifying the AcoupiProgram as demonstrated below:

```
    MyWorkerConfig = acoupi.programs.WorkerConfig(
        workers=[acoupi.programs.AcoupiWorker(name="recording"), ...]
    )

    class MyProgram(acoupi.programs.AcoupiProgram):
        worker_config = MyWorkerConfig
        ...
```

This approach allows precise control over task distribution and resource
allocation within your **acoupi** programs. If not specified, a single worker is created by default.

## 2. Running Programs

**acoupi** utilizes [**Celery**](https://docs.celeryq.dev/en/stable/index.html) as the framework to organize tasks and schedules. To ensure program reliability,
especially in the face of system events like reboots, we employ systemd for
managing system services.

Running a program with Celery involves designating a Celery app [`celery.Celery`](/src/acoupi/system.apps.py). **acoupi** streamlines this process by creating an `app.py Python script based on user configurations. This script acts as a bridge to expose the necessary Celery app. By using the 
[``acoupi.system.get_celery_app()``](/src/acoupi/system.apps.py) function, the script loads the [``acoupi.programs.AcoupiProgram``](/src/acoupi/programs.base.py) and user configurations, then runs the setup method to incorporate user-defined tasks into the Celery app.

Simultaneously, Acoupi generates bash scripts to launch, stop, and restart Celery workers, complete with suitable configurations as specified in the **acoupi** program. ``systemd`` utilizes these scripts to manage **acoupi** services,
ensuring reliable execution. This orchestration ensures integration of **acoupi** programs into the system.

## 3. Where is the Program Data Stored?

Acoupi manages program setups through a dedicated directory known as ``ACOUPI_HOME``, specially designated to house all Acoupi-related files. By default, ``ACOUPI_HOME`` is situated at the following location:

```
    $HOME/.acoupi
```

Whenever a new **acoupi** program and its configurations are set up, the contents within this folder adapt accordingly to the new specifications. It's important to note that the user need not actively interact with these files, and their existence is ideally kept hidden to prevent unintended modifications that might disrupt system functionality.

The files in ``ACOUPI_HOME`` are created by **acoupi** using templates from the [`acoupi/templates`](/src/acoupi/templates/) folder. These templates are filled with user-provided configurations using the  [**Jinja2**](https://jinja.palletsprojects.com/en/3.1.x/) template engine. This
makes sure that the files in ``ACOUPI_HOME`` match the user's settings accurately. The code generation process is handled by the `acoupi.system.setup_program()` function.

The structure of the ``ACOUPI_HOME`` directory is as follows:

```
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

The ``logs`` directory stores the logs generated by Celery workers during program execution. Meanwhile, the ``run`` directory houses the PID (process ID) files of currently running jobs.

