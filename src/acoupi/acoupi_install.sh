#!bin/bash
#sudo apt update
#sudo apt upgrade
export USER=$USER
export HOME=$HOME

# Install git and other packages
echo "Installing dependencies"
sudo apt install git alsa-utils libasound2-dev wget cmake sqlite3 #pulseaudio 
# Install python3 and python3 libs
sudo apt install python3-dev python3-pip python3-venv python3-pyaudio

# Move to home directory
cd ~
echo "Cloning Acoupi repository - Main branch" 
branch=main
git clone -b $branch --depth=1 https://github.com/audevuilli/acoupi.git ${HOME}/acoupi

# Move to git directory
# cd ~/acoupi
# Create a virtual python environment
#echo "Establishing a python virtual environment"
#python3 -m venv acoupi
#source ./acoupi/bin/activate

# Install pyaudio using install_pyaudio.sh script
echo "Installing pyaudio"
bash $HOME/acoupi/src/acoupi/script/install_pyaudio.sh

# Install packages with pip
echo "Installing libraries package"
#pip3 install -U -r $HOME/src/acoupi/requirements.txt
pip3 install . 

# Setup Configuration
# echo "Set config parameters to run acoupi"
# echo "STEP 1: Please enter the device timezone as Continent/City (e.g. Europe/London)"
# read DEFAULT_TIMEZONE
# 
# echo "STEP 2: Please enter your microphone sampling rate (e.g. 192000)"
# read DEFAULT_SAMPLE_RATE
# 
# echo "STEP 3: Please enter the daily START time for recordings."
# echo "Note that if start time is after end time - recordings will run overnight."
# echo "Enter in format hh:mm:ss (e.g 19:00:00)"
# read START_RECORDING
# 
# echo "STEP 4: Please enter the daily END time for recordings."
# echo "Enter in format hh:mm:ss (e.g 08:00:00)"
# read END_RECORDING
# 
# echo "STEP 5: Please enter the detection probability threshold for species detection."
# echo "Note that robustness of the probability of detection varied from species to species."
# echo "Threshold between 0 and 1. Threshold of 0.7 is recommended. Set lower/higher"
# read DEFAULT_THRESHOLD
# 
# echo "STEP 6: MQTT Server Parameters. Please ignore if MQTT Server not use"

# Store the configuration variables in a config file
# file="$HOME/acoupi/src/acoupi/acoupi.config"
# echo 'DEFAULT_TIMEZONE' >> $file
# echo DEFAULT_SAMPLE_RATE >> $file
# echo 'START_RECORDING' >> $file
# echo 'END_RECORDING' >> $file
# echo DEFAULT_THRESHOLD >> $file
# 
# echo "Thanks! config file created at $HOME/acoupi/src/acoupi/acoupi.config"
# echo ""

# Move the .service files to lib/systemd/system - Enable and Start it
echo "Installing Acoupi Services"
# Move acoupi_run.service into systemd
#sudo ln -sf $HOME/acoupi/src/acoupi/services/acoupi_run.service /usr/lib/systemd/system
sudo ln -sf $HOME/acoupi/src/acoupi/services/acoupi_testing.service /usr/lib/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable acoupi_testing.service
sudo systemctl start acoupi_testing.service
#systemctl status acoupi_testing.service

echo "Acoupi Setup Complete!"
echo "***************************************"
echo "Please reboot your device to start acoupi service - use sudo reboot"