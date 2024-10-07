# Deployment

After installing and configuring an _acoupi_ program, users can proceed to deploy it. This means the device will start running the program, ensuring audio recordings happen according to the configured recording schedule, recorded files will be saved or deleted, and if the _connected_ program was configured, messages will be sent to a remote server. 
 
??? Tip "What happens when a deployment starts?" 

    When starting the deployment of a program, _acoupi_ will do the following:

    - __Create Storages__: This step checks that the folders and database files to store recordings and metadata exist. If using the _default_ program configuration, a `storages/` folder will be created in the home directory (i.e., `home/pi/`), containing a `metadata.db` file and a `recordings/` folder to store the `.wav` audio files. 
    - __Schedule Tasks__: This step creates special instructions called systemd unit files to ensure that the program runs automatically in the background. This means the program will keep running even when the terminal window is closed or the device restarts after power interruption.

??? tip "How are deployments managed?"

    For more details about the system background processes and the management of a deployment, refer to the [_Explanation: System_](../explanation/system.md) section.



## Managing the deployment of _acoupi_ programs via the CLI

The video shows how a user can start, stop, and get the status of _acoupi_ programs.

![type:video](../img/acoupi_deployment.mp4){: style='width: 100%'}

### Before starting a deployment

Before starting a deployment, it's important to run a health check to ensure there are no errors in the program configuration. If everything is in order, a green message saying __`Health checks passed`__ will be printed. However, if there are any errors, the system will display specific error messages. To resolve them, modify the configurations settings according to the provided error messages. 

!!! Example "CLI Command: pre-deployment checks"

    ```bash
    acoupi check
    ```

### Starting a deployment

When ready to start a program, use the `acoupi deployment start` command. This will prompt you to provide some additional information; a name for the deployment and the latitude and longitude coordinates of the device’s location. This data will be saved in the `metadata.db` file along with the start date and time of the deployment.

!!! Example "CLI Command: activating an acoupi program"

    ```bash
    acoupi deployment start
    ```
??? Info "Table: Additional parameters when starting a deployment"

    | __Deployment Parameter__ | Type | Value | Definition|
    | --- | --- | --- | ---|
    | `name`| string | - | Name for the specific deployment.| 
    | `latitude`| float | - | The latitude coordinate of the device location when   deployed. | 
    |`longitude`| float | - | The longitude coordinate of the device location when  deployed. | 

### Getting the status of a deployment

After starting a deployment, it’s good practice to check the status of the program by running the `acoupi deployment status` command. This command can show the following outputs: 

- _`active (running)`_ in green meaning that everything is working well
- _`inactive (dead)`_ colourless meaning that the program is not running. Run the start command to active it. 
- _`failed (Result: exit-code)`_ in red meanting that there is an error with running the program. Read the error messages to troubleshoot the issue. 

!!! Example "CLI Command: viewing the status of an acoupi program"

    ```bash
    acoupi deployment status
    ```

### Stopping a deployment

Stopping the deployment can be necessary if you need to modify the program’s configuration, move the device to a different location, or fix any errors that have appeared in the logs. To halt the program, use the `acoupi deployment stop` command. Remember, once a deployment is stopped, it can only be restarted by running the acoupi deployment start command again.

!!! Example "CLI Command: halting an acoupi program"

    ```bash
    acoupi deployment stop
    ```
