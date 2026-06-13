# Contributing

Acoupi is a community effort to facilitate access to bioacoustic models and ease their on-device deployment for field surveys. 

**We warmly welcome contributions, suggestions, fixes and constructive feedback to both acoupi code and documentation.**

## Development Setup

Clone the repository and install the development environment with `uv`:

```bash
uv sync --locked --all-extras --dev
```

This installs the project, documentation tooling, test dependencies, and the local developer tools used by the repository.

## Local Checks

Run the full lint suite:

```bash
make lint
```

This currently runs:

- `ty` for static type checking
- `ruff` for linting

Run the test suite:

```bash
make test
```

Build the documentation locally:

```bash
make docs
```

Serve the documentation locally while writing docs:

```bash
make serve-docs
```
