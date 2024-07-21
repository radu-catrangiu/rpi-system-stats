#!/bin/bash

# Variables
SERVICE_NAME=rpi-stats-influx-n-grafana
SERVICE_DESCRIPTION="Raspberry Pi InfluxDb & Grafana Containers"
SCRIPT_DIR=$(dirname "$(realpath "$0")")
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
CURRENT_USER=$(whoami)  # Get the current user's username
GROUP=$(id -gn)  # Get the current user's group name
DOCKER_PATH=$(which docker)

# Check if Docker Compose is installed
if [ -z "$DOCKER_PATH" ]; then
  echo "Docker is not installed. Please install Docker first."
  exit 1
fi

# Create the systemd service unit file
sudo bash -c "cat > $SERVICE_FILE <<EOF
[Unit]
Description=$SERVICE_DESCRIPTION
After=network.target

[Service]
WorkingDirectory=$SCRIPT_DIR
ExecStart=$DOCKER_PATH compose up
ExecStop=$DOCKER_PATH compose down
Restart=always
User=$CURRENT_USER
Group=$GROUP

[Install]
WantedBy=multi-user.target
EOF"

# Reload systemd to pick up the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable $SERVICE_NAME.service

# Start the service immediately
sudo systemctl start $SERVICE_NAME.service

# Check if rpi-stats-harvester service exists
if systemctl list-units --type=service | grep -q 'rpi-stats-harvester.service'; then
  echo "rpi-stats-harvester service exists. Ensuring it is started..."
  sudo systemctl start rpi-stats-harvester.service
else
  echo "rpi-stats-harvester service does not exist. Installing it now..."

  if [ -f "$SCRIPT_DIR/stats-harvester-py/install.sh" ]; then
    echo "Waiting for rpi-stats-influx-n-grafana to be fully running..."
    while ! systemctl is-active --quiet $SERVICE_NAME.service; do
      sleep 5
      echo "Checking if $SERVICE_NAME is running..."
    done

    echo "$SERVICE_NAME is running. Proceeding with the installation of rpi-stats-harvester..."
    bash "$SCRIPT_DIR/stats-harvester-py/install.sh"
  else
    echo "Error: stats-harvester-py/install.sh not found!"
    exit 1
  fi
fi

# Check the status of the services
echo "Checking status of $SERVICE_NAME service..."
sudo systemctl status --no-pager -l $SERVICE_NAME.service | head -n 20
