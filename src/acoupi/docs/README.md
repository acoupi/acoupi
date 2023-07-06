## Setup BatDetect2 on RPi
#
1. Install raspbian OS - 64-bit lite on SDCard

2. Setup RPI with username and password

3. Make variable user and home system directory
```
export USER=$USER
export HOME=$HOME
```

4. Check system update and upgrade
```
sudo apt update && sudo apt upgrade
````
5. Install dependencies
```
sudo apt install git alsa-utils portaudio19-dev libsndfile1 libasound2-dev wget cmake
```
6. Install python3 and python3 libs
```
sudo apt install python3-dev python3-pip python3-venv python3-pyaudio
```

7. Move to home directory if not and clone the Acoupi GitHub repository (main) branch 
```
cd ~
git clone -b main --depth=1 https://audevuilli@github.com/audevuilli/acoupi.git ${HOME}/acoupi
```

8. Install dependencies with pip in acoupi folder
```
cd acoupi
pip install update -U pip
pip install -e .
pip install batdetect2
```

9. Test if batdetect2 main.py work. 

10. Start service to run acoupi-batdetect2
bash $HOME/acoupi/src/acoupi/scripts/setup_service.sh