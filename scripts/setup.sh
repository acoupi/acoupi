#!/bin/bash

sudo apt update
sudo apt install -y \
    alsa-utils \
    libasound2-dev \
    libffi-dev \
    python3-pyaudio \
    portaudio19-dev \
    rabbitmq-server

# Check if CI or GITHUB_RUN_ID are not set (i.e. running locally)
# and if so run sudo loginctl enable-linger
if [ -z "$CI" ] && [ -z "$GITHUB_RUN_ID" ]; then
    sudo loginctl enable-linger
    pip install --upgrade pip
    pip install acoupi
fi
