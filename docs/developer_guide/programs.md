# Programs 

In the context of Acoupi, a program consists of a structured collection of tasks orchestrated to establish a distinct configuration for acoustic monitoring. Acoupi offers users the flexibility to either develop custom programs or deploy existing ones, detailed instructions for which can be found in the program reference.

Programs are represented as importable subclasses of `acoupi.programs.AcoupiProgram`. Any module accessible via the Python
path that contains an `AcoupiProgram` class is eligible for program deployment. Users designate the desired program by providing the corresponding module name (e.g., `acoupi.programs.custom.test`). Acoupi facilitates class loading using the [`acoupi.system.load_program()`](/src/acoupi/system/programs.py) function.

Programs encompass three essential components: tasks, configuration schema, and worker configuration. Tasks outline the operations within the program. A configuration schema defines the program's configuration structure, and worker configuration governs task execution.

## Program Configuration

Each program within **acoupi** can be accompanied by a configuration schema. This schema serves as a blueprint, delineating the structure and data types of configuration variables. Implementation of the schema is realized through a `pydantic.BaseModel` object.

When configuring a program for execution within the **acoupi** framework, the associated configuration schema plays a crucial role. The schema guides the user through the definition of essential fields, facilitated by the utilization of [`acoupi.system.parse_config_from_args()`](/src/acoupi/system/parsers.py) function. These configurations are subsequently stored for reference.

During program execution, **acoupi** leverages the stored configurations. As the program starts, these configurations are loaded and provided to the program using the [`acoupi.system.AcoupiProgram.setup()`](/src/acoupi/system/programs/base.py) method. This instantiation process ensures that the program is equipped with accurate and pertinent configurations.