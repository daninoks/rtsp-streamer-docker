#!/bin/bash
# [[ $# != 1 ]] && echo "Error: Wrong argument list. (e.g.: ./run_rtsp_streamer.sh video.mp4)" && exit 1

videosArray=("$@")

# echo "INFO: videos passed:"
for video in ${videosArray[@]}; do
  echo "$video"
done

for video in ${videosArray[@]}; do
  if ! [[ -f $video ]]; then
    echo "ERROR: '$video' file does not exist."
    exit 1
  fi
done

# Ports list:
# Change lower ports and port range here:
firstBroadcastPort=50000
firstInternalPort=51000
portsRange=30

# Max port value calculate:
lastBroadcastPort=$firstBroadcastPort+$portsRange
lastInternalPort=$firstInternalPort+$portsRange

# Init ports list:
allOuterPorts=( $firstBroadcastPort )
allInerPorts=( $firstInternalPort )

# Fill ports list:
for ((port = $firstBroadcastPort; port <= $lastBroadcastPort; port++)); do
  allOuterPorts+=( $port )
  #allOuterPorts[${#allOuterPorts[@]}]=$port
done
echo "All Outer Ports:\n ${allOuterPorts[@]}"

# Fill ports list:
for ((port = $firstInternalPort; port <= $lastInternalPort; port++)); do
  allInerPorts+=( $port )
done
echo "All Inner Ports:\n ${allInerPorts[@]}"

# Check availiable ports:
function innerPorts() {
  for item in ${allOuterPorts[@]}; do
    if [[ $(netstat -tlpn 2>/dev/null | grep "$item" | awk '{print $4}') == '' ]]; then
      freeOuterPort=$item
      break
    fi
  done
}

function outerPorts() {
  for item in ${allInerPorts[@]}; do
    if [[ $(netstat -tlpn 2>/dev/null | grep "$item" | awk '{print $4}') == '' ]]; then
      freeInerPort=$item
      break
    fi
  done
}

innerPorts
outerPorts
# echo "INFO: freeInerPort: $freeInerPort"
# echo "INFO: freeOuterPort: $freeOuterPort"

# Stream configuration:
test_video="$1"
ffserver_cfg="${1}_ffserver.config"

function configure_ffserver {
  echo "
HTTPPort $freeInerPort
HTTPBindAddress 0.0.0.0
MaxHTTPConnections 2000
MaxClients 1000
MaxBandwidth 5000000
CustomLog -

RTSPPort $freeOuterPort
RTSPBindAddress 0.0.0.0

<Stream test>
    Format rtp
    File \"$test_video\"
</Stream>
" > $ffserver_cfg
}

# MAIN functionality
FFSERVER_CMD="ffserver"

# Change FFserver CMD for MacOS
[[ "$(uname)" == "Darwin" ]] && FFSERVER_CMD="./mac_os/bin/ffserver"
configure_ffserver

# Run stream:
server_ip=$(ip address | grep inet | grep /24 | awk '{print $2}' | sed 's/\/24//g')
echo -e "Running RTSP streamer on (rtsp://${server_ip}:${freeOuterPort}/test)"
$FFSERVER_CMD -f $ffserver_cfg

# Kill streams on exit:
function kill_streams {
  killall ffmpeg
  echo "all ffmpeg streams killed"
}
trap kill_streams INT