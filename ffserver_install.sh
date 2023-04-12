#!/bin/bash
#        
# 
#
apt install git curl wget ffmpeg make gcc yasm screen net-tools -y
echo "Bash: Required packages istalled"
git clone https://git.ffmpeg.org/ffmpeg.git ffmpeg
echo "Bash: https://git.ffmpeg.org/ffmpeg.git cloned to ./ffmpeg"
cd ffmpeg
echo "Bash: Working dir is ./ffmpeg"
git checkout 2ca65fc7b74444edd51d5803a2c1e05a801a6023
echo "Bash: Checkout done. (2ca65fc7b74444edd51d5803a2c1e05a801a6023)"
sleep 1
./configure
echo "Bash: Configure finished."
sleep 1
make -j4
echo "Bash: Make finished"
sleep 1
mv ffserver /bin/ffserver
echo "Bash: ffserver moved to /bin/"
sleep 1
