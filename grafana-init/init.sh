#!/bin/sh

# Define the source and destination directories
SOURCE_DIR="/script/config"
DEST_DIR="/grafana/conf"

mkdir -p "$DEST_DIR"

# Copy everything from SOURCE_DIR to DEST_DIR, replacing existing files
cp -rf "$SOURCE_DIR"/* "$DEST_DIR"

# Change the ownership of all files and directories in DEST_DIR to the user with UID 1001
chown -R 1001:1001 "$DEST_DIR"

# Print a message indicating the operation is complete
echo "All files from $SOURCE_DIR have been copied to $DEST_DIR, replaced if existing, and ownership changed to UID 1001."


echo Printing /grafana/conf/provisioning contents:
ls -la /grafana/conf/provisioning
echo 

echo Printing /grafana/conf/provisioning/datasources contents:
ls -la /grafana/conf/provisioning/datasources
echo

echo Printing /grafana/conf/provisioning/dashboards contents:
ls -la /grafana/conf/provisioning/dashboards
echo

echo Printing /grafana/conf contents:
ls -la /grafana/conf
echo 

echo Printing /grafana/conf/dashboards_to_import contents:
ls -la /grafana/conf/dashboards_to_import
echo