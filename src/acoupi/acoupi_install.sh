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
# cd ~
# echo "Cloning Acoupi repository - Main branch" 
# branch=main
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
#sudo -u ${USER} mkdir -p audio/audio_files
#sudo -u ${USER} mkdir -p audio/analysed

# Move the .service files to lib/systemd/system - Enable and Start it
services = ("acoupi_audiorec.service" 
            "acoupi_runmodel.service"
            "acoupi_saveresults.service"
            "acoupi_senddata.service")

for service in "${services[@]}"
do 
    sudo ln -sf $HOME/acoupi/services/$service /usr/lib/systemd/system
    sudo systemctl enable $service
    sudo systemctl start $service

    systemctl is-active --quiet $service && echo acoupi services are running || echo acoupi services are not running
done
