## Acoupi Software Architecture

Acoupi software is divided into two parts; the code base framework and the running application.
The **_acoupi framework_** is organised into a layered architecture that ensures standardisation of data while providing flexibility of configuration.
The **_acoupi application_** provides a simple command line interface (CLI) allowing users to configure the acoupi framework for deployment.

### Acoupi Framework

The **acoupi** framework has been designed to provide maximum flexibility and keep away the internal complexity from a user.
The framework is made of four intricate elements, which we call the data schema, components, tasks, and programs.

The figure below provides a simplified example of an acoupi program.
This program illustrates some of the most important data schema, components, and tasks.

![Figure 2: Example of a simplified acoupi program.](img/acoupi_program_simplified.png) _Figure 2: Example of a simplified acoupi program._

Refer to the [**Developer Guide**](docs/developer_guide/index.md) section of the documentation for full details on each of these elements.

### Acoupi Application

An acoupi application consists of the full set of code that runs at the deployment stage.
This includes a set of scripts made of an acoupi program with user configurations, celery files to organise queues and workers, and bash scripts to start, stop, and reboot the application processes.
An acoupi application requires the acoupi package and related dependencies to be installed before a user can configure and run it.
The figure below gives an overview of key stages related to the installation, configuration and runtime of an acoupi application.

![Figure 3: Overview of steps to follow to install, configure, and start an acoupi application.](img/acoupi_installation_steps.png) _Figure 3: Overview of steps to follow to install, configure, and start an acoupi application._

## Features and development

**acoupi** builds on other Python packages.
The list of the most important packages and their functions is summarised below.
For more information about each of them, make sure to check their respective documentation.

- [PDM](https://pdm-project.org/2.10/) to manage package dependencies.
- [Pydantic](https://docs.pydantic.dev/dev/) for data validation.
- [Pytest](https://docs.pytest.org/en/7.4.x/) as a testing framework.
- [Pony-ORM](https://ponyorm.org/) for databse queries.
- [Celery](https://docs.celeryq.dev/en/stable/getting-started/introduction.html) to manage the processing of tasks.
- [Jinja](#jinja) for text templating.
