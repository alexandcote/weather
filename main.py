#!/usr/bin/env python
import os
import time
import serial
import requests
import logging
import logging.handlers

from weather import Weather
from PyCRC.CRCCCITT import CRCCCITT
from raven.conf import setup_logging
from raven.handlers.logging import SentryHandler

ACK = '\x06'
DEVICE = None
logger = logging.getLogger(__name__)


def init(dsn):
    handler = SentryHandler(dsn)
    syslog_handler = logging.handlers.SysLogHandler(address='/dev/log')

    logger.setLevel(logging.INFO)
    handler.setLevel(logging.WARN)

    logger.addHandler(syslog_handler)
    setup_logging(handler)


def initialize_communication():
    count = 0

    logger.info("Weather.Reader: Start the communication with the device")

    while count < 3:
        DEVICE.write('\n')
        x = DEVICE.readline()

        if x == '\r\n':
            logger.info("Weather.Reader: Communication established")
            return True

        logger.info("Weather.Reader: Communication failed {0}".format(count))

        time.sleep(1.2)
        count += 1

    return False


def read_data():
    logger.info("Weather.Reader: Read Data")

    if initialize_communication():
        DEVICE.write('LOOP 1\n')

        if DEVICE.read(2)[-1] == ACK:
            logger.info("Weather.Reader: Device ACK")

            data = DEVICE.read(99)
            if CRCCCITT().calculate(data) == 0:
                logger.info("Weather.Reader: CRC is valid: {data}".format(
                    data=data))
                return Weather(data)
            else:
                logger.warning("Weather.Reader: CRC not valid")
        else:
            logger.warning("Weather.Reader: Device don't ACK")
    else:
        logger.warning('Weather.Reader: Initialization failed')

    return None


def send_data(server_token, server_url, data):
    logger.info("Weather.Reader: Send data to the api server")

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
        logger.warning(
            "Can't add new data in the database. HTTP code : {status}".format(
                status=response.status_code))
    else:
        logger.info(
            "Weather.Reader: The data was add : {response}".format(
                response=response))


def main():
    global DEVICE

    sleep = float(os.getenv('WEATHER_SLEEP', 60))
    dsn = os.getenv('WEATHER_SENTRY_DSN', '')
    port = os.getenv('WEATHER_DEVICE_PORT', '/dev/ttyUSB0')
    server_url = os.getenv('WEATHER_SERVER_URL', '')
    server_token = os.getenv('WEATHER_SERVER_TOKEN', '')

    init(dsn)

    logger.info("Weather.Reader: Initialization")

    DEVICE = serial.Serial(
        port=port,
        baudrate=19200,
        timeout=1.2
    )

    while True:
        weather = read_data()

        if weather:
            if weather.is_valid():
                send_data(server_token, server_url, weather.to_dict())
                logger.info("Weather.Reader: Sleep for {0} seconds".format(sleep))
                time.sleep(sleep)
            else:
                logger.warning("Weather.Reader: Weather data is invalid")
        else:
            logger.warning("Weather.Reader: Weather is empty")

        # Clean memory
        del weather


if __name__ == "__main__":
    main()
