# acoupi
Classifier for bioacoustics devices. 

## Diagram

![diagram](acoupi.svg)

## Development

### Package dependencies

We are using [pdm](https://pdm.fming.dev/latest/) to manage package dependencies. In order to install the package and all dependencies (including the development dependencies) run the command

    pdm install
  
To add a dependencies to the package run

    pdm add <dependency1> ...
  
make sure to commit and uplaod both the changes to the pyproject.toml file and the pdm.lock.

To add development-only dependencies run

    pdm add -d <dev_dependency1> ...

### Testing

We are using [pytest](https://docs.pytest.org/en/7.2.x/) as a test runner. All tests are in the `test` directory. To run the suite of tests run the command

    pdm run pytest
  
 Running through `pdm` will insure that the acoupi package and all its dependencies are loaded before running the tests.
