#!/usr/bin/env python

import os
import time
import subprocess
import datetime
import psutil
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

def get_temperature():
    try:
        # Execute the vcgencmd command
        result = subprocess.run(['/usr/bin/vcgencmd', 'measure_temp'], capture_output=True, text=True)

        # Check if the command was successful
        if result.returncode != 0:
            print("Error: vcgencmd command failed")
            return None

        # Parse the output
        output = result.stdout.strip()
        if output.startswith("temp=") and output.endswith("'C"):
            # Extract the temperature value
            temp_str = output.split('=')[1].strip("'C")
            try:
                temperature = float(temp_str)
                return temperature
            except ValueError:
                print("Error: Failed to parse temperature value")
                return None
        else:
            print("Error: Unexpected output format")
            return None
    except FileNotFoundError:
        print("Error: /usr/bin/vcgencmd not found")
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None


def get_data():
    # take a timestamp for this measurement
    now = datetime.datetime.utcnow()

    uptime_hours = (time.time() - psutil.boot_time())/3600
    uptime_days = uptime_hours / 24

    # collect some stats from psutil
    disk = psutil.disk_usage('/')
    mem = psutil.virtual_memory()
    load = psutil.getloadavg()
    cpu_temp = get_temperature()
    
    if cpu_temp is None:
        cpu_temp = float(-1)
    
    # Collect network stats
    net_stat = psutil.net_io_counters(pernic=True, nowrap=True)["eth0"]
    net_in_1 = net_stat.bytes_recv
    net_out_1 = net_stat.bytes_sent
    time.sleep(1)
    net_stat = psutil.net_io_counters(pernic=True, nowrap=True)["eth0"]
    net_in_2 = net_stat.bytes_recv
    net_out_2 = net_stat.bytes_sent

    net_in = round((net_in_2 - net_in_1) / 1024 / 1024, 3)
    net_out = round((net_out_2 - net_out_1) / 1024 / 1024, 3)

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
            "mem_free": mem.free,
            "mem_used": mem.used,
            "cpu_temp": cpu_temp,
            "eth0_in": net_in,
            "eth0_out": net_out,
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
        print(f"Error: {e}")
        return None, None

def write_data(client, bucket, point):
    try:
        write_api = client.write_api(write_options=SYNCHRONOUS)
        write_api.write(bucket=bucket, record=point)
    except Exception as e:
        print(f"Error writing data: {e}")

if __name__ == "__main__":
    try:
        interval_str = os.getenv('INTERVAL_SECONDS')
        # interval_str = "15"
        if interval_str is None:
            raise ValueError("INTERVAL_SECONDS environment variable not set")
        
        interval = int(interval_str)
        if interval <= 0:
            raise ValueError("INTERVAL_SECONDS must be a positive integer")

        print(f"Writing to InfluxDB every {interval} seconds. Press Ctrl+C to stop.")

        client, bucket = get_influxdb_client()
        if client and bucket:
            while True: 
                data = get_data()
                write_data(client, bucket, data)
                time.sleep(interval)
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
