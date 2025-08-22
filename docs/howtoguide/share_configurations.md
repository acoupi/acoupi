# Share Configuration

## Introduction

This guide will show you how to share configurations between different `acoupi`-powered devices so you can deploy multiples devices with the same exact behaviour.
This can also help you replicate a study or keep track of how the device was configured during a deployment.

Here's what we'll cover:

1.  [What are configuration files?](#1_what_are_configuration_files)
2.  [Where are configuration files stored?](#2_where_are_configuration_files_stored)
3.  [How to view the configuration?](#3_how_to_view_the_configuration)
4.  [How to edit the configuration?](#4_how_to_edit_the_configuration)
5.  [How to share configurations?](#5_how_to_share_configurations)
6.  [Applying a new configuration?](#6_applying_a_new_configuration)

## 1. What are configuration files?

`acoupi` uses configuration files to store the settings for a program.
These files are in JSON format and are created when you run the `acoupi setup` command.

The main configuration files are:

- `program.json`: Stores the program-specific settings, such as the microphone settings, recording schedule, and any other parameters defined by the program.
- `celery.json`: Stores the configuration for the Celery workers, which are responsible for running the tasks in the background.
- `program.name`: A simple text file that contains the name of the program that is currently configured (e.g., `acoupi.programs.default`).

## 2. Where are configuration files stored?

By default, `acoupi` stores its configuration files in the `~/.acoupi` directory.
The directory structure looks like this:

```
/home/user/.acoupi/
├── config/
│   ├── celery.json
│   ├── deployment.json
│   ├── env
│   ├── name
│   └── program.json
├── log/
├── run/
└── app.py
```

The main configuration files are located in the `config` subdirectory.
You can change the location of the home directory by setting the `ACOUPI_HOME` environment variable.
For example, if you set `ACOUPI_HOME` to `/my/custom/acoupi/dir`, then `acoupi` will look for its configuration files in `/my/custom/acoupi/dir/config`.

## 3. How to view the configuration

To view the current configuration of your `acoupi` program, you can use the `acoupi config get` command.
This command will print the entire configuration in JSON format.

```bash
acoupi config get
```

Here is an example of the output for the `acoupi.programs.default` program:

```json
{
  "timezone": "Europe/London",
  "microphone": {
    "device_name": "UltraMic 250K 16 bit r4",
    "samplerate": 250000,
    "audio_channels": 1
  },
  "recording": {
    "duration": 10,
    "interval": 30,
    "chunksize": 8192,
    "schedule_start": "04:00:00",
    "schedule_end": "23:00:00"
  },
  "paths": {
    "tmp_audio": "/run/shm",
    "recordings": "/home/pi/storages/recordings",
    "db_metadata": "/home/pi/storages/metadata.db"
  },
  "recording_saving": {
    "starttime": "11:00:00",
    "endtime": "15:00:00",
    "before_dawndusk_duration": 30,
    "after_dawndusk_duration": 30,
    "frequency_duration": 0,
    "frequency_interval": 0
  }
}
```

You can also view a specific field by using the `--field` option:

```bash
acoupi config get --field recording.duration
```

## 4. How to edit the configuration

The `acoupi` command-line interface (CLI) provides commands for viewing and editing the configuration of your program.
For a detailed explanation of how to use these commands and a list of the available configuration parameters, please refer to the [Configuration Tutorial](../tutorials/configuration.md).

This guide will focus on how to manage and share the configuration files themselves.
As a quick reminder, you can view your configuration with `acoupi config get` and change a value with `acoupi config set --field <parameter_name> <new_value>`.

While the CLI is the safest way to edit your configuration, you can also edit the `program.json` file directly.
This is useful when you want to make multiple changes at once.
You can find this file in the `~/.acoupi/config` directory.

## 5. How to share configurations

Once you have configured your `acoupi` program, you may want to share this configuration with other devices or keep a backup for future use.
Here are two ways to do this:

### a) Navigate the SD card on your computer

If you have physical access to the device, the easiest way to get the configuration is to shut down the device, take out the SD card, and plug it into your computer.
The configuration files are located in the `~/.acoupi/config` directory on the SD card.

You can then copy the entire `config` directory to your computer or to another SD card.

### b) Copy the files remotely (via scp)

If you have remote access to the device, you can use the `scp` command to copy the configuration files over the network.
`scp` is a secure file transfer protocol that is available on most Linux and macOS systems. For a detailed guide on how to use `scp`, you can refer to [this guide](https://snapshooter.com/learn/linux/copy-files-scp).

To copy the configuration files from the remote device to your local machine, you can use the following command:

```bash
scp -r pi@<remote_device_ip>:~/.acoupi/config ~/acoupi_config_backup
```

Replace `<remote_device_ip>` with the IP address of your remote device.
This will copy the entire `config` directory to a new directory called `acoupi_config_backup` in your home directory.

To copy the configuration from your local machine to a remote device, you can use the following command:

```bash
scp -r ~/acoupi_config_backup pi@<remote_device_ip>:~/.acoupi/config
```

## 6. Applying a new configuration

After you have copied a new configuration to a device, you need to apply the changes.
If the device is already running a deployment, you should first stop it and then start it again.
If the device is not running a deployment, you can simply start one.

To stop the current deployment, run:

```bash
acoupi deployment stop
```

Then, to start the deployment with the new configuration, run:

```bash
acoupi deployment start
```

This will start the Celery workers, which will then load the new configuration.
Your `acoupi` device will now be running with the new settings.

To verify that the new configuration has been loaded correctly, you can use the `acoupi config get` command.
This will print the current configuration to the console, so you can check that the values have been updated.
