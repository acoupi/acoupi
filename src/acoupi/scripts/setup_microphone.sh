#!/bin/bash

# Prompt the user to select the desired input device
echo "Select the input device:"
arecord -l

echo -n "Enter device index: "
read device_index

# Update the config file - add the selected input device
echo "DEVICE_INDEX = $device_index" >> config.py
