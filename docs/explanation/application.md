# Programs (acoupi framework)

A **Program** is a full application that runs on a device.
It consists of a structured collection of tasks orchestrated to establish a distinct configuration for acoustic monitoring.

Programs encompass three essential elements: tasks, configuration schema, and worker configuration.
Tasks outline the operations within the program.
A configuration schema defines the program's configuration structure, and worker configuration governs task execution.

Programs are represented as importable subclasses of [`acoupi.programs.AcoupiProgram`][acoupi.programs.AcoupiProgram].
Any module accessible via the Python path that contains an `AcoupiProgram` class is eligible for program deployment.
Users designate the desired program by providing the corresponding module name (e.g., `acoupi.programs.custom.test`).
Acoupi facilitates class loading using the [`acoupi.system.load_program()`][acoupi.system.load_program] function.

??? Tip

    Acoupi offers users the flexibility to either develop custom programs or deploy existing ones, detailed instructions for which can be found in the program reference.

## Program Configuration

Each program within **acoupi** can be accompanied by a configuration schema.
This schema serves as a blueprint, delineating the structure and data types of configuration variables.
Implementation of the schema is realized through a `pydantic.BaseModel` object.

When configuring a program for execution within the **acoupi** framework, the associated configuration schema plays a crucial role.
The schema guides the user through the definition of essential fields, facilitated by the utilization of [`acoupi.system.parse_config_from_args()`][acoupi.system.parse_config_from_args] function.
These configurations are subsequently stored for reference.

During program execution, **acoupi** leverages the stored configurations.
As the program starts, these configurations are loaded and provided to the program using the [`acoupi.system.AcoupiProgram.setup()`][acoupi.programs.AcoupiProgram.setup] method.
This instantiation process ensures that the program is equipped with accurate and pertinent configurations.

## Pre-Built Programs

**Acoupi** provides currently two prebuilt programs:

- The [**BatDetect2**](https://github.com/acoupi/acoupi_batdetect2) program to record and classify UK Bats species.
- The [**BirdNET**](https://github.com/acoupi/acoupi_batdetect2) program to record and classify bird species.
