# Raspberry PI System Stats 

This project is meant to collect stats from a Raspberry Pi and feed them into an InfluxDB instance in order to be represented in a Grafana dashboard.

## Required files before startup

Below are example files required for the project to function.

When deploying please change sensitive values like `tokens` or `passwords`.

### Path: `{project_dir}/.env`

```ini
INFLUXDB_DB=statsdb
INFLUXDB_ADMIN_USER=admin
INFLUXDB_ADMIN_USER_PASSWORD=admin_password
INFLUXDB_ADMIN_USER_TOKEN=admin_token
INFLUXDB_HTTP_AUTH_ENABLED=true

GF_SECURITY_ADMIN_PASSWORD=bitnami

INFLUXDB_URL=http://influxdb:8086 # Here we use `InfluxDB` because this .env file is used in Docker compose
INFLUXDB_TOKEN=admin_token
INFLUXDB_ORG=primary
INFLUXDB_BUCKET=primary
```

### Path: `{project_dir}/stats-harvester-py/.env`

```ini
HARVEST_INTERVAL_SECONDS=5
INFLUXDB_URL=http://localhost:8086 # Here we use `localhost` because `stats-harvester-py` runs on host
INFLUXDB_TOKEN=admin_token
INFLUXDB_ORG=primary
INFLUXDB_BUCKET=primary
```

## How to run?

Simply run `bash install.sh` in the project directory.

## How it works?

This project installs **two** `systemd` services in order to collect system stats and display them in a Grafana dashboard.

There are 2 components:

1. `rpi-stats-influx-n-grafana.service`
2. `rpi-stats-harvester.service` 

### rpi-stats-influx-n-grafana.service

This component is made of a `docker-compose.yaml` file that sets up an InfluxDB instance and a Grafana instance based on the environment variables provided in the `.env` file from the root of the project.

The Grafana instance uses a "init container" to run the script in `grafana-init` directory. This script is supposed to initialize the datasource and setup everything so that the stats dashboard is easily accesible.


### rpi-stats-harvester.service

This service depends on `rpi-stats-influx-n-grafana.service`.

This component is made of a Python script that uses the [psutil](https://pypi.org/project/psutil/) library to obtain data about the system and publish it to the InfluxDB instance.

## Notes

* ### Currently the InfluxDB bucket retention is set to `Forever` it needs to be changed _manually_ **!** 

* Initially I wanted to make this project delivaerable using only `docker compose`, but the script that collects data uses files from the Linux `/proc` File System which is *kind of special*. 
    * It can be mounted on a Docker container, but because of the way the `/proc` File System works it won't be able to retrieve some stats that belong to the host machine.
    * Basically, when reading a file in the `/proc` directory, there isn't an actual file being read, but instead it's delivering real time data about structures in the Kernel.
        * Because of this, when a container tries to read a "file" from the `/proc` "directory" it will actually get information from its own Kernel.
* As a solution, I resorted to deploying everything as `systemd` services. This way the dashboard should start up automagically after every reboot.
