#!/bin/bash
echo "╔══╣ Install: kokoro_tts_ros (STARTING) ╠══╗"

sudo apt update -y

sudo apt install -y ros-humble-vision-msgs

pip3 install soundfile

pip3 install pygame

sudo apt install espeak-ng

pip3 install kokoro==0.9.4
pip3 install misaki[en,ja]==0.9.4

cd ~/colcon_ws/src/

git clone -b humble-devel https://github.com/TeamSOBITS/sobits_msgs.git

echo "╚══╣ Install: kokoro_tts_ros (FINISHED) ╠══╝"
