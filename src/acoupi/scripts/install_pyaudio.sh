#!/bin/sh
sudo apt update 
sudo apt upgrade 

#Move to home directiory
cd ~

#Create a directory to install some pacakges 
mkdir -p install
cd install
 
echo "Downloading PyAudio..."
wget -c http://people.csail.mit.edu/hubert/pyaudio/packages/pyaudio-0.2.8.tar.gz
tar zxf pyaudio-0.2.8.tar.gz
rm pyaudio-0.2.8.tar.gz
cd PyAudio-0.2.8

# echo "Installing portaudio..."
# wget -c http://www.portaudio.com/archives/pa_stable_v19_20140130.tgz
# tar zxf pa_stable_v19_20140130.tgz
# mv portaudio portaudio-v19
# cd portaudio-v19
# ./configure
# make
# cd ..

echo "Building..."
#export CFLAGS="-I `pwd`/portaudio-v19/include/ -L `pwd`/portaudio-v19/lib/.libs/"
python setup.py build --static-link
python setup.py install

#remove install directory
rm -rf /media/sdcard/setup/install
rm -rf install

echo "PyAudio installed."
