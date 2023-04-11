#!/bin/bash
#        
# Run from parent ffmpeg.
#
apt install git curl wget ffmpeg make gcc yasm screen net-tools -y
#pacman -Suy git curl wget ffmpeg yasm
git clone https://git.ffmpeg.org/ffmpeg.git ffmpeg
cd ffmpeg
git checkout 2ca65fc7b74444edd51d5803a2c1e05a801a6023
sudo apt-get install yasm
sleep 1
./configure
sleep 1
make -j4
sleep 1
mv ffserver /bin/ffserver
sleep 1
ffserver