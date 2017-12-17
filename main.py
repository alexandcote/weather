#!/usr/bin/env python
import time
import serial
import argparse
import requests
import logging
import logging.handlers
import struct

from weather import Weather
from PyCRC.CRCCCITT import CRCCCITT
from raven.conf import setup_logging
from raven.handlers.logging import SentryHandler

ACK = '\x06'
SLEEP = 10
device = None
logger = logging.getLogger(__name__)

def init(dsn):
    handler = SentryHandler(dsn)
    syslog_handler = logging.handlers.SysLogHandler(address = '/dev/log')

    logger.setLevel(logging.INFO)
    handler.setLevel(logging.WARN)

    logger.addHandler(syslog_handler)
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

    logger.info("Weather.Reader: Start the communication with the device")

    while count < 3:
        device.write('\n')
        x = device.readline()

        if x == '\r\n':
            logger.info("Weather.Reader: Communication etablished")
            return True

        logger.info("Weather.Reader: Communcaation failed {0}".format(count))

        time.sleep(1.2)
        count += 1

    return False

def read_data():
    logger.info("Weather.Reader: Read Data")
    if initialize_communication():
        device.write('LOOP 1\n')

        if device.read(2)[-1] == ACK:
            logger.info("Weather.Reader: Device ACK")

            data = device.read(99)
            if CRCCCITT().calculate(data) == 0:
                logger.info("Weather.Reader: CRC is valid: {data}".format(
                    data=data))
                return Weather(data)
            else:
                logger.warn("Weather.Reader: CRC not valid")
        else:
            logger.warn("Weather.Reader: Device don't ACK")
    else:
        logger.warn('Weather.Reader: Initialization failed')

    return None

def send_data(server_token, server_url, data):
    headers = {
        'Authorization': server_token,
        'Content-Type': 'application/json'
    }
    logger.info("Weather.Reader: Send data to the api server")
    response = requests.post(
        server_url,
        json=dict(data=data),
        headers=headers
    )

    if response.status_code != 201:
        logger.warn(
            "Can't add new data in the database. HTTP code : {status}".format(
                status=response.status_code))
    else:
        logger.info(
            "Weather.Reader: The data was add : {response}".format(
                response=response))
def main():
    global device
    args = valid_args()
    init(args.dsn)

    logger.info("Weather.Reader: Initialization")

    device = serial.Serial(
        port = args.device_port,
        baudrate = 19200,
        timeout = 1.2
    )

    while True:
        weather = read_data()
        if weather:
            send_data(args.server_token, args.server_url, weather.toDict())
            logger.info("Weather.Reader: Sleep for {0} seconds".format(SLEEP))
            time.sleep(SLEEP)
        else:
            logger.warn("Weather.Reader: Weather is empty")

if __name__ == "__main__":
    main()
