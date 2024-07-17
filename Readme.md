# Raspberry PI System Stats 

This project is meant to harvest stats from a Raspberry Pi 4 and feed them into an InfluxDB instance in order to be represented in a Grafana dashboard.

## Temperature reading test

```bash
docker run -it --rm \
    -v /usr/bin/vcgencmd:/usr/bin/vcgencmd \
    -e LD_LIBRARY_PATH=/usr/lib \
    --device /dev/vchiq \
    --device /dev/vcio \
    debian:bookworm \
    /usr/bin/vcgencmd measure_temp
```