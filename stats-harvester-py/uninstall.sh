#!/bin/bash

# Variables
SERVICE_NAME=rpi-stats-harvester
SCRIPT_DIR=$(dirname "$(realpath "$0")")
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
VENV_PATH="$SCRIPT_DIR/venv"

# Stop the service if it's running
sudo systemctl stop $SERVICE_NAME.service

# Disable the service to prevent it from starting on boot
sudo systemctl disable $SERVICE_NAME.service

# Remove the systemd service unit file
sudo rm $SERVICE_FILE

# Reload systemd to pick up the changes
sudo systemctl daemon-reload

# Deactivate and remove the virtual environment
if [ -d "$VENV_PATH" ]; then
  rm -rf $VENV_PATH
fi

# Provide feedback
echo "Service $SERVICE_NAME has been uninstalled."
