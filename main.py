#!/usr/bin/env python
import time
import serial
import argparse
import requests
import logging
import struct

from weather import Weather
from PyCRC.CRCCCITT import CRCCCITT
from raven.conf import setup_logging
from raven.handlers.logging import SentryHandler

ACK = '\x06'
device = None
logger = logging.getLogger(__name__)

def init(dsn):
    handler = SentryHandler(dsn)
    handler.setLevel(logging.WARN)
    setup_logging(handler)

def valid_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('device_port',  help='Device Port, (i.e: /dev/ttyUSB0)')
    parser.add_argument('server_url',  help='Server URL, (i.e: https://my_server.com/api/new_data)')
    parser.add_argument('server_token',  help='Server Token, (i.e: Bearer <token>')
    parser.add_argument('dsn',  help='Server Token, (i.e: https://xxx@sentry.io/<project> <token>')
    args = parser.parse_args()
    return args

def initialize_communication():
    count = 0

    while count < 3:
        device.write('\n')
        x = device.readline()

        if x == '\r\n':
            return True

        time.sleep(1.2)
        count += 1

    return False

def read_data():
    if initialize_communication():
        device.write('LOOP 1\n')

        if device.read(2)[-1] == ACK:
            response = device.read(99)
            if CRCCCITT().calculate(response) == 0:
                return Weather(response)
            else:
                logger.warn('CRC not valid')
        else:
            logger.warn('Error in the read data')
    else:
        logger.warn('Initialization failed')

    return None

def send_data(server_token, server_url, data):
    headers = {
        'Authorization': server_token,
        'Content-Type': 'application/json'
    }

    response = requests.post(
        server_url,
        json=dict(data=data),
        headers=headers
    )

    if response.status_code != 201:
        logger.warn(
            "Can't add new data in the database. HTTP code : {status}".format(
                status=response.status_code))

def main():
    global device
    args = valid_args()
    init(args.dsn)

    device = serial.Serial(
        port = args.device_port,
        baudrate = 19200,
        timeout = 1.2
    )

    while True:
        weather = read_data()
        if weather:
            send_data(args.server_token, args.server_url, weather.toDict())
            time.sleep(60)

if __name__ == "__main__":
    main()
