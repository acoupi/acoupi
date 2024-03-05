# Acoupi CLI

The Acoupi Command-Line Interface (CLI) serves as the essential bridge between acoupi users and acoupi backend, facilitating interaction with the acoupi system. Utilizing the CLI simplifies the process of program setup and management.

Executing `acoupi setup` initiates the configuration stage. Within this phase,
users can opt for a specific program to run and provide any necessary
configurations. This process triggers the `acoupi.system.setup_program()`
function, which automates the creation of essential files within `ACOUPI_HOME`,
aligning them with the user's selections. 

The CLI also offers the following commands:

- **`acoupi start`**: leverages systemctl to ensure that the associated services
  are respectively enabled. This command is used to start program execution.
- **`acoupi stop`**: leverages systemctl to ensure that the associated services
  are respectively disabled. This command is used to halt program execution.
- **`acoupi status`**: shows the status of the associated acoupi services.
- **`acoupi config`**: has subcommands to manage acoupi configuration.
  - `acoupi config show`: show the user-defined configuration of an acoupi
    program.
  - `acoupi config get`: prints a specific configuration value. Command requires
    the user to input the specific configuration parameter name.
  - `acoupi config sub`: allows the user to modify the value of a specific
    configuration field. Command requires the user to input the specific
    configuration parameter name and the new value for it.
