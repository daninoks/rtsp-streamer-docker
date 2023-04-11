ANIMATION_SEQUENCE="/-\|"

for package in curl wget net-tools vim git build-essential software-properties-common; do
  # Run the package installation command with the animation
sudo apt-get install -y ${package} > /dev/null 2>&1 &
# Run the animation loop while the package is being installed
while ps -p $! > /dev/null; do
for i in $(seq 0 ${#ANIMATION_SEQUENCE}); do
# Print the current animation frame
echo -ne "\r[${ANIMATION_SEQUENCE:$i:1}] Installing ${package}... "
# Simulate some processing time
sleep 0.1
done
done
# Print a message when the package is installed
echo -e "\r[${ANIMATION_SEQUENCE:0:1}] ${package} installed."
done