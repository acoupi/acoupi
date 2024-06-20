# Acoupi CLI

The acoupi CLI is your primary tool for managing bioacoustic detection models
on edge devices. Use it to configure, deploy, and monitor your Acoupi programs.

!!! tip

    For the full list of commands and their options refer to the [CLI Reference](../reference/cli.md).

## Setup

Guides you through the initial setup process, allowing you to select the program and adjust its settings.

```bash
acoupi setup --program <program_name>
```

## Health Check

Performs pre-deployment checks to ensure your configuration is correct.

```bash
acoupi check
```

## Start Deployment

Deploys and activates the selected program on your edge device.

```bash
acoupi start
```

## Stop Deployment

Stops the running program.

```bash
acoupi stop
```

## System Status

Displays the current status of your Acoupi program (running, stopped, etc.).

```bash
acoupi status
```

## Configuration

### Show Configuration

Displays your current configuration settings.

```bash
acoupi config show
```

### Get Configuration

Retrieves the value of a specific configuration parameter (e.g., acoupi config get sampling_rate).

```bash
acoupi config get <parameter_name>
```

### Modify Configuration

Modifies the value of a specific configuration parameter (e.g., `acoupi config sub sampling_rate 22050`).

```bash
acoupi config sub <parameter_name> <new_value>
```
