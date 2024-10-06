# Deployment

Once acoupi has been installed and configured on a device, users can proceed to deploy the program. This means the device will begin to record audio according to the chosen recording schedule, manage saving and deleting of audio files, and if the _connected_ program was configured, send messages to a remote server. 
 
## What happens during deployment? 

- __Running Tasks__: The device will handle audio recording, manage files such as saving and deleting, and if the _connected_ program was configured, send messages to a remote sever. 
- __Create Storage__: A new folder named `storages/` will be created in the home directory. This folder will contain database files such as `metadata.db` and `messaging.db`, and a `recordings` folder to save the `.wav` audio files. 

Starting the deployment of a program means that 

- Before disconnecting, it is good practice to ensure that the program is running correclty. This can be done by checking the status of the program (i.e., the status of acoupi services). Use the command `status` to pring the status of the services. If everything is green and at the line: Active: `active (running)` then everything is working well. If something is showing up in orange or red, read the error message to understand what is going wrong. 

- now that the program is running, users can leave the device do it job. This means that a user can disconnect from the `ssh session` and the terminal window they have been working on to setup the device. To close the connection without shuting down the device use the command `control D` on Mac OS. 

- users have the options to stop a deployment. Stopping a deployment can be useful, if users for example want to modify some of the configuration parameters, move the device to a different location, or simply ends the collection of data. The command to use is `deployment stop`. Note that if a deployment is stopped, the only way to start a deployment again, is by entering the `deployment start` command. 

The deployment of an _acoupi program_ generates two systemd unit files to manage the start, restart, and stop of an _acoupi_ program.

## Managing _acoupi_ deployment via the CLI

### Starting a deployment

!!! Example "CLI Command: activating an acoupi program"

    ```bash
    acoupi deployment start
    ```

### Stopping a deployment

!!! Example "CLI Command: halting an acoupi program"

    ```bash
    acoupi deployment stop
    ```

### Getting the status of a deployment

!!! Example "CLI Command: viewing the status of an acoupi program"

    ```bash
    acoupi deployment status
    ```


The video shows how a user can start, stop, and get the status of an _acoupi_ program using the command line interface.

![type:video](../img/acoupi_deployment.mp4){: style='width: 100%'}

??? tip "How are deployments managed?"

    To learn more about how the system manage a deployment, refer to the [_Explanation: System_](../explanation/system.md/#3-orchestration) section.
