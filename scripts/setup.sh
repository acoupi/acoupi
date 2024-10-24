#!/bin/bash
echo "Installing system dependencies."
sudo apt update
sudo apt install -y \
    alsa-utils \
    libasound2-dev \
    libffi-dev \
    python3-dev \
    python3-pyaudio \
    portaudio19-dev \
    rabbitmq-server

# Exit early if running in CI.
if [ -n "$CI" ] && [ -n "$GITHUB_RUN_ID" ]; then
    exit 0
fi

echo "Enabling linger for the current user."
sudo loginctl enable-linger

if ! command -v "uv" > /dev/null 2>&1; then
    echo "Installing uv to manage python environments."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

echo "Installing acoupi!"
uv tool install acoupi

echo "Updating shell."
uv tool update-shell
source $HOME/.bashrc
