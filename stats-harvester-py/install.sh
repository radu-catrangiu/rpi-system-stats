#!/bin/bash

# Variables
SERVICE_NAME=rpi-stats-harvester
SCRIPT_DIR=$(dirname "$(realpath "$0")")
SCRIPT_PATH="$SCRIPT_DIR/harvest.py"
WORKING_DIRECTORY="$SCRIPT_DIR"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
CURRENT_USER=$(whoami)  # Get the current user's username
VENV_PATH="$WORKING_DIRECTORY/venv"
REQUIREMENTS_FILE="$WORKING_DIRECTORY/requirements.txt"
ENV_FILE="$SCRIPT_DIR/.env"

# Check if the requirements.txt file exists
if [ ! -f "$REQUIREMENTS_FILE" ]; then
  echo "requirements.txt file not found!"
  exit 1
fi

# Check if the .env file exists
if [ ! -f "$ENV_FILE" ]; then
  echo ".env file not found!"
  exit 1
fi

# Create a virtual environment using venv
python3 -m venv $VENV_PATH

# Activate the virtual environment and install required packages
source $VENV_PATH/bin/activate
pip install --upgrade pip  # Upgrade pip to ensure compatibility
pip install -r $REQUIREMENTS_FILE
deactivate

# Read environment variables from .env file
ENV_VARS=$(awk -F= '{print "Environment=" $1 "=\"" $2 "\""}' $ENV_FILE)

# Create the systemd service unit file
echo "[Unit]
Description=Raspberry Pi Stats Harvester
After=network.target rpi-stats-influx-n-grafana.service
Requires=rpi-stats-influx-n-grafana.service

[Service]
ExecStart=$VENV_PATH/bin/python $SCRIPT_PATH
WorkingDirectory=$WORKING_DIRECTORY
StandardOutput=inherit
StandardError=inherit
Restart=always
User=$CURRENT_USER
$ENV_VARS

[Install]
WantedBy=multi-user.target" | sudo tee $SERVICE_FILE

# Reload systemd to pick up the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable $SERVICE_NAME.service

# Start the service immediately
sudo systemctl start $SERVICE_NAME.service

# Check the status of the service
sudo systemctl status $SERVICE_NAME.service
