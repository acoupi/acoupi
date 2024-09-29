# Programs (acoupi application)

A **Program** constists of a structured collection of tasks orchestrated to establish a distinct configuration for acoustic monitoring.
A **program** forms the core of an acoupi application that runs on a device.

Programs encompass three essential elements: tasks, configuration schema, and worker configuration.
Tasks outline the operations within the program.
A configuration schema defines the program's configuration structure, and worker configuration governs task execution.

Programs are represented as importable subclasses of [`acoupi.programs.core.AcoupiProgram`][acoupi.programs.core.AcoupiProgram].
Any module accessible via the Python path that contains an `AcoupiProgram` class is eligible for program deployment.
Users designate the desired program by providing the corresponding module name (e.g., `acoupi.programs.test`).
Acoupi facilitates class loading using the [`acoupi.system.load_program()`][acoupi.system.load_program] function.

<figure markdown="span">
    ![Figure 1: Overview of acoupi application](../img/acoupi_program_application.png){ width="90%" }
    <figcaption><b>Overview of an acoupi application.</b> A configuration schema provides the settings to run acoupi program's tasks. Acoupi workers are configured to orchestrate and execute the tasks.
</figure>

!!! Tip Acoupi offers users the flexibility to either develop your own custom programs or deploy existing ones.
Please refer to the [_Tutorials: Pre-Built Programs_](../tutorials/programs.md) for a step-by-step guide to deploy and use existing programs, and the [_How-to Guides: Programs_](../howtoguide/programs.md) for detailed instructions on how to develop your own custom programs.

## Program Configuration

Each program within **acoupi** is accompanied by a configuration schema.
This schema serves as a blueprint, delineating the structure and data types of the configuration variables.
Implementation of the schema is realized through a `pydantic.BaseModel` object.

When configuring a program for execution within the **acoupi** framework, the associated configuration schema plays a crucial role.
The schema guides the user through the definition of essential fields, facilitated by the utilisation of [`acoupi.system.parse_config_from_args()`][acoupi.system.parse_config_from_args] function.
These configurations are subsequently stored for reference.

During program execution, **acoupi** leverages the stored configurations.
As the program starts, these configurations are loaded and provided to the program using the [`acoupi.system.AcoupiProgram.setup()`][acoupi.programs.AcoupiProgram.setup] method.
This instantiation process ensures that the program is equipped with accurate and pertinent configurations.

!!! Example

    ```python

    class Program(AcoupiProgram):

        config: ConfigSchema
        """Configuration Schema for a test program."""

        worker_config = WorkerConfig()
        """Configuration for acoupi workers."""

        def setup(self, config: ConfigSchema):
            """Setup an acoupi program."""

            """Assign configuration schema to components."""
            self.component = components.ComponentName()
            self.model = ModelName()

            """Create the tasks."""
            task_name = tasks.generate_task_name(
                component=self.component,
                model=self.model,
                logger=self.logger.getChild("task_name"),
            )

            """Register tasks to queues."""
            self.add_task(
                function=task_name,
                schedule=datetime.timedelta(),
                queue="queue_name",
            )
    ```

## Pre-Built Programs

**Acoupi** provides currently two prebuilt programs:

- The [**BatDetect2**](https://github.com/acoupi/acoupi_batdetect2) program to record and classify UK Bats species.
- The [**BirdNET**](https://github.com/acoupi/acoupi_batdetect2) program to record and classify bird species.

!!! Tip Refer to the pre-built programs documentation if you are looking to use them.
