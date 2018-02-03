import json
import struct


class Weather:
    def __init__(self, data):
        self.barometer = float(self.get_two_bytes(data, 7)) / 1000
        self.bar_trend = self.get_sign(data, 3)
        self.in_temperature = float(self.get_two_bytes(data, 9)) / 10
        self.out_temperature = float(self.get_two_bytes(data, 12)) / 10
        self.in_humidity = self.get_sign(data, 11)
        self.out_humidity = self.get_sign(data, 33)
        self.rain_rate = self.get_two_bytes(data, 41)
        self.ten_min_wind_speed = self.get_unsign(data, 15)
        self.wind_direction = self.get_two_bytes(data, 16)
        self.wind_speed = self.get_unsign(data, 14)
        self.uv = self.get_sign(data, 43)
        self.solar_radiation = self.get_two_bytes(data, 44)
        self.storm_rain = self.get_two_bytes(data, 46)
        self.start_date_storm = self.get_date(data, 48)
        self.day_rain = self.get_two_bytes(data, 50)
        self.month_rain = self.get_two_bytes(data, 52)
        self.year_rain = self.get_two_bytes(data, 54)
        self.day_et = self.get_two_bytes(data, 56)
        self.month_et = self.get_two_bytes(data, 58)
        self.year_et = self.get_two_bytes(data, 60)
        self.inside_alarm = self.get_sign(data, 70)
        self.rain_alarm = self.get_sign(data, 71)
        self.outside_alarm = self.get_two_bytes(data, 72)
        self.transmitter_battery = self.get_sign(data, 86)
        self.console_battery = self.get_voltage(data, 87)
        self.forecast_icon = self.get_sign(data, 89)
        self.forecast_rule_number = self.get_sign(data, 90)
        self.time_of_sunrise = self.get_time(data, 91)
        self.time_of_sunset = self.get_time(data, 93)

    def get_sign(self, data, offset):
        return struct.unpack('b', data[offset])[0]

    def get_unsign(self, data, offset):
        return struct.unpack('B', data[offset])[0]

    def get_two_bytes(self, data, offset):
        return struct.unpack('<h', ''.join([data[offset], data[offset + 1]]))[0]

    def get_date(self, data, offset):
        value = self.get_two_bytes(data, offset)
        if value != -1:
            month = int(bin(value)[-4:], 2)
            day = int(bin(value)[-8:-4], 2)
            year = int(bin(value)[-15:-8], 2) + 2000
            return "{year}-{month:02d}-{day:02d}".format(
                year=year, month=month, day=day)
        return None

    def get_time(self, data, offset):
        value = self.get_two_bytes(data, offset)
        hours = value % 100
        minutes = value - (hours * 100)
        return "{hours:02d}:{minutes:02d}".format(hours=hours, minutes=minutes)

    def get_voltage(self, data, offset):
        value = self.get_two_bytes(data, offset)
        return float((value * 300) / 512) / 100

    def toDict(self):
        return self.__dict__

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
            sort_keys=True, indent=4)
