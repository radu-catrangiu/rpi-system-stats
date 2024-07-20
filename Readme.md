# Raspberry PI System Stats 

This project is meant to harvest stats from a Raspberry Pi 4 and feed them into an InfluxDB instance in order to be represented in a Grafana dashboard.

## Required files before startup

### .env
```ini
INFLUXDB_DB=statsdb
INFLUXDB_ADMIN_USER=admin
INFLUXDB_ADMIN_USER_PASSWORD=admin_password
INFLUXDB_ADMIN_USER_TOKEN=admin_token
INFLUXDB_HTTP_AUTH_ENABLED=true

GF_SECURITY_ADMIN_PASSWORD=bitnami

INTERVAL_SECONDS=10
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=admin_token
INFLUXDB_ORG=primary
INFLUXDB_BUCKET=primary
```
