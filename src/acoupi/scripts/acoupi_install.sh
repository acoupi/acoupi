#!bin/bash
#sudo apt update
#sudo apt upgrade
export USER=$USER
export HOME=$HOME

# Install git and other packages
echo "Installing dependencies"
sudo apt install git alsa-utils libasound2-dev wget cmake #pulseaudio 
# Install python3 and python3 libs
sudo apt install python3-dev python3-pip python3-venv python3-pyaudio

# Move to home directory
# cd ~
# echo "Cloning Acoupi repository - RPi branch" 
# branch=rpi
# git clone -b rpi --depth=1 https://github.com/audevuilli/acoupi.git ${HOME}/acoupi
# git clone -b $branch --depth=1 https://github.com/audevuilli/acoupi.git ${HOME}/acoupi

# Move to git directory
# cd ~/acoupi
# Create a virtual python environment
#echo "Establishing a python virtual environment"
#python3 -m venv acoupi
#source ./acoupi/bin/activate

# Install pyaudio using install_pyaudio.sh script
echo "Installing pyaudio"
bash $HOME/src/acoupi/script/install_pyaudio.sh

# Install packages with pip
echo "Installing libraries package"
#pip3 install -U -r $HOME/src/acoupi/requirements.txt
pip3 install . 

## Install sqlite database
#sudo apt install sqlite3
## Create a new database file 
#sqlite3 acoupi.db
## Create all the necessary tables in acoupi.db

# Create directory to store audio files
#echo "Creating necessary directories"
#sudo -u ${USER} mkdir -p src/acoupi/storage/bats
#sudo -u ${USER} mkdir -p src/acoupi/storage/no_bats

