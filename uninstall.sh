#!/bin/bash

# Variables
SERVICE_NAME=rpi-stats-influx-n-grafana
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
HARVESTER_SERVICE_NAME=rpi-stats-harvester
HARVESTER_INSTALL_SCRIPT="./stats-harvester-py/uninstall.sh"
SCRIPT_DIR=$(dirname "$(realpath "$0")")

# Check if rpi-stats-harvester service is running
if systemctl list-units --type=service | grep -q "$HARVESTER_SERVICE_NAME.service"; then
  echo "$HARVESTER_SERVICE_NAME service is running. Proceeding with uninstallation..."
  if [ -f "$HARVESTER_INSTALL_SCRIPT" ]; then
    sudo bash "$HARVESTER_INSTALL_SCRIPT"
  else
    echo "Error: $HARVESTER_INSTALL_SCRIPT not found!"
    exit 1
  fi
else
  echo "$HARVESTER_SERVICE_NAME service is not running. No need to uninstall."
fi

# Stop the service if it is running
echo "Stopping $SERVICE_NAME service..."
sudo systemctl stop $SERVICE_NAME.service

# Disable the service
echo "Disabling $SERVICE_NAME service..."
sudo systemctl disable $SERVICE_NAME.service

# Remove the systemd service file
echo "Removing $SERVICE_NAME service file..."
sudo rm -f $SERVICE_FILE

# Reload systemd to remove the service
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload
