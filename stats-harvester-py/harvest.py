#!/usr/bin/env python

import os
import time
import datetime
import signal
import sys
import logging
import psutil
from influxdb_client import InfluxDBClient, Point
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

def get_cpu_usage():
    cpu_usages = psutil.cpu_percent(percpu=True)

    points = []
    for i, usage in enumerate(cpu_usages):
        point = Point("cpu_usage") \
            .tag("core", f"core_{i}") \
            .field("usage_percent", usage)
        points.append(point)

    return points

def get_disk_io_usage():
    disk_to_allow = ["sda"]
    disks = psutil.disk_io_counters(perdisk=True)

    points = []
    for disk, value in disks.items():
        if disk not in disk_to_allow:
            continue;

        point = Point("disk_io_usage") \
            .tag("disk", disk) \
            .field("read_bytes", value.read_bytes) \
            .field("write_bytes", value.write_bytes)
        
        points.append(point)

    return points

def get_disk_usage():
    disk = psutil.disk_usage('/')

    point = Point("disk_usage") \
        .field("disk_percent", disk.percent) \
        .field("disk_free", disk.free) \
        .field("disk_used", disk.used)
    
    return [point]

def get_memory_usage():
    mem = psutil.virtual_memory()

    point = Point("memory_usage") \
        .field("mem_percent", mem.percent) \
        .field("mem_total", mem.total) \
        .field("mem_used", mem.used)
    
    return [point]

def get_sensor_temperatures():
    temps = psutil.sensors_temperatures()

    points = []
    for sensor, readings in temps.items():
        for reading in readings:
            point = Point("sensor_temperatures") \
                .tag("sensor", sensor) \
                .tag("label", reading.label) \
                .field("current", reading.current) \
                .field("high", reading.high) \
                .field("critical", reading.critical)
    
            points.append(point)

    return points


def get_system_info(): 
    uptime_hours = (time.time() - psutil.boot_time())/3600
    
    point = Point("system_info") \
        .field("uptime_hours", uptime_hours)
    
    return [point]

def get_net_stats():
    net_stat = psutil.net_io_counters(pernic=True)

    points = []
    for interface, values in net_stat.items():
        point = Point("net_stats") \
            .tag("interface", interface)
        
        values_dict = values._asdict()
        for key in values_dict.keys():
            point.field(key, values_dict[key])
        
        points.append(point)

    return points

def get_data():
    # take a timestamp for this measurement
    now = datetime.datetime.utcnow()

    uptime_hours = (time.time() - psutil.boot_time())/3600

    # collect some stats from psutil
    disk = psutil.disk_usage('/')
    mem = psutil.virtual_memory()
    load = [x / psutil.cpu_count() * 100 for x in psutil.getloadavg()]
    cpu_temp = psutil.sensors_temperatures().get("cpu_thermal")[0].current

    if cpu_temp is None:
        cpu_temp = float(-1)
    
    # Collect network stats
    net_stat = psutil.net_io_counters(nowrap=True)

    # collect disk usage stats
    disk_stat = psutil.disk_io_counters(perdisk=False)

    # format the data as a single measurement for influx
    point = {
        "measurement": "raspberrypi",
        "time": now,
        "fields": {
            "load_percent_over_1m": load[0],
            "load_percent_over_5m": load[1],
            "load_percent_over_15m": load[2],
            "disk_percent": disk.percent,
            "disk_free": disk.free,
            "disk_used": disk.used,
            "disk_read_bytes": disk_stat.read_bytes,
            "disk_write_bytes": disk_stat.write_bytes,
            "mem_available": mem.available,
            "mem_percent": mem.percent,
            "mem_total": mem.total,
            "mem_used": mem.used,
            "cpu_temp": cpu_temp,
            "net_bytes_in": net_stat.bytes_recv,
            "net_bytes_out": net_stat.bytes_sent,
            "uptime_hours": uptime_hours
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
                points = []
                points += get_cpu_usage()
                points += get_disk_io_usage()
                points += get_disk_usage()
                points += get_memory_usage()
                points += get_sensor_temperatures()
                points += get_system_info()
                points += get_net_stats()
                data = get_data()
                points += [data]
                write_data(client, bucket, points)
                time.sleep(interval)
    except ValueError as e:
        logging.error(f"ValueError: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")