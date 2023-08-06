.. _acoupi-quickstart:

Quickstart
==========

Installing Acoupi
-----------------

Before you can use **Acoupi**, you'll need to install it on your device. Don't
worry, it's easy! Just make sure you have a network connection and ``wget``
installed, and then run the following command:

.. code-block:: sh

    wget -O - https://raw.githubusercontent.com/audevuilli/acoupi/master/install.sh | sh

This will download all the necessary dependencies and install **Acoupi** on
your device.

Configuring Acoupi
------------------

Once you have **Acoupi** installed, it's time to configure it. First, type:

.. code-block:: sh

    acoupi setup

This will show you a list of available **Acoupi** programs. Pick the one you
want by typing its number and pressing enter. Acoupi will then take you through
a series of questions to configure your program.

If you want to use a custom configuration file, you can do so by typing:

.. code-block:: sh

    acoupi setup --program <program-name> --config-file <path-to-config-file>

.. note::

    If you want to create your own **Acoupi** program, follow the instructions
    in the :ref:`advanced guide<advanced-guide>`.

To check your program's current configuration, type:

.. code-block:: sh

    acoupi config show

And to modify your program's configuration, type:

.. code-block:: sh

    acoupi config edit

Deploying Acoupi
----------------

Once your **Acoupi** program is configured, it's time to deploy it! Just type:

.. code-block:: sh

   acoupi deployment start

You can check the status of your deployment by typing:

.. code-block:: sh

    acoupi deployment status

And if you need to stop your deployment, just type:

.. code-block:: sh

   acoupi deployment stop

And that's it! You're now ready to use **Acoupi** to deploy your very own
bioacoustic monitoring system. Happy monitoring!
