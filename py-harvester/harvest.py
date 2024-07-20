#!/usr/bin/env python

import os
import time
import datetime
import signal
import sys
import logging
import psutil
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S"
)

def signal_handler(sig, frame):
    logging.info(f"Signal received: {signal.strsignal(sig)}")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


def get_data():
    # take a timestamp for this measurement
    now = datetime.datetime.utcnow()

    uptime_hours = (time.time() - psutil.boot_time())/3600
    uptime_days = uptime_hours / 24

    # collect some stats from psutil
    disk = psutil.disk_usage('/')
    mem = psutil.virtual_memory()
    load = psutil.getloadavg()
    cpu_temp = psutil.sensors_temperatures().get("cpu_thermal")[0].current

    if cpu_temp is None:
        cpu_temp = float(-1)
    
    # Collect network stats
    net_stat = psutil.net_io_counters(pernic=True, nowrap=True)["eth0"]
    eth0_bytes_in = net_stat.bytes_recv
    eth0_bytes_out = net_stat.bytes_sent

    # format the data as a single measurement for influx
    point = {
        "measurement": "raspberrypi",
        "time": now,
        "fields": {
            "load_1": load[0],
            "load_5": load[1],
            "load_15": load[2],
            "disk_percent": disk.percent,
            "disk_free": disk.free,
            "disk_used": disk.used,
            "mem_percent": mem.percent,
            "mem_available": mem.available,
            "mem_total": mem.total,
            "mem_used": mem.used,
            "cpu_temp": cpu_temp,
            "eth0_bytes_in": eth0_bytes_in,
            "eth0_bytes_out": eth0_bytes_out,
            "uptime_hours": uptime_hours,
            "uptime_days": uptime_days
        }
    }

    return point

def get_influxdb_client():
    try:
        # Get connection details from environment variables
        url = os.getenv('INFLUXDB_URL')
        token = os.getenv('INFLUXDB_TOKEN')
        org = os.getenv('INFLUXDB_ORG')
        bucket = os.getenv('INFLUXDB_BUCKET')

        if not all([url, token, org, bucket]):
            raise ValueError("Missing one or more InfluxDB environment variables")

        # Create the InfluxDB client
        client = InfluxDBClient(url=url, token=token, org=org)
        return client, bucket
    except Exception as e:
        logging.error(f"Error: {e}")
        return None, None

def write_data(client, bucket, point):
    try:
        write_api = client.write_api(write_options=SYNCHRONOUS)
        write_api.write(bucket=bucket, record=point)
    except Exception as e:
        # print(f"Error writing data: {e}")
        logging.error(f"Error writing data: {e}")

if __name__ == "__main__":
    try:
        interval_str = os.getenv('HARVEST_INTERVAL_SECONDS')
        if interval_str is None:
            data = get_data()
            print(data)
            sys.exit(0)
        
        interval = int(interval_str)
        if interval <= 0:
            raise ValueError("HARVEST_INTERVAL_SECONDS must be a positive integer")

        logging.info(f"Writing to InfluxDB every {interval} seconds.")

        client, bucket = get_influxdb_client()
        if client and bucket:
            while True: 
                data = get_data()
                write_data(client, bucket, data)
                time.sleep(interval)
    except ValueError as e:
        logging.error(f"ValueError: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
