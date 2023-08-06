Installation
============

To install acoupi in your board and all required dependencies run the following command:

.. code-block:: bash

    wget -O- https://raw.githubusercontent.com/audevuilli/acoupi/master/install.sh | bash


After installation, you might want to install some additional Acoupi programs to run on your device.
This can be done with pip, for example:

.. code-block:: bash

    pip install acoupi-batdetect2

Follow this link to see a list of some of the available programs. Sometimes
the programs might have some additional or different installation requirements.
We recommend reading the documentation of the program you want to install.

To check that the installation was successful, you can run the
following command:

.. code-block:: bash

    acoupi --help

This should print the help message of the acoupi program.
