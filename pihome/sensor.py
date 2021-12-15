#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Sensor data manager for PiHome
File: sensor
Project: PiHome
File Created: Friday, 29th October 2021 7:02:14 pm
Author: Aziz Contractor
-----
MIT License

Copyright (c) 2021 Your Company

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
-----
"""
import board
import adafruit_dht
import datetime as dt
import logging
from typing import TYPE_CHECKING, Any, Dict
import pihome.constants as constants

from pihome.db import DBMgr
from pihome.log import log_dict

if TYPE_CHECKING:
    from pihome.vault import VaultMgr

_LOG = logging.getLogger(__name__)


class SensorMgr:
    """
    This class manages gathering data from environment sensors and adding it to the database. The
    data is gathered using the Raspberry Pi Sense Hat. The SenseHat class makes it simple to gather
    sensor data. Ensure that I2C is enabled before using this module.

    Attributes:
        location (str): The relative location of the sensor. Used to distinguish multiple sensors
            at the same home.
        dht (adafruit_dht.DHT22): The sensor module used to query sensors.
        db (DBMgr): The database module to add data to the DB.
    """

    __VAULT_ROOT = "sensor/"
    __SENSOR_TABLE = "environment"
    __AVAIL_LOCATIONS = ["upstairs", "downstairs", "attic"]

    __DHT_PIN = board.D24

    def __init__(self, vault: "VaultMgr", location: str) -> None:
        """
        Initializes the sensor manager. Allows it to start monitoring sensor data.

        Args:
            vault (VaultMgr): Used to connect to the vault and get secrets.
            location (str): The location of the device.
        """
        if location not in self.__AVAIL_LOCATIONS:
            raise ValueError(
                f"Invalid location {location}. Must be one of {self.__AVAIL_LOCATIONS}"
            )
        _LOG.info(f"Initializing Sensor Manager.")
        self.dht = adafruit_dht.DHT22(self.__DHT_PIN)
        self.location = location
        self.__vault = vault
        self.__connect_to_database()

    def exit(self):
        """
        Exits the sensor manager. Calls the DB exit method to close DB connection.
        """
        self.db.exit()
        try:
            self.dht.exit()
        except Exception as ex:
            _LOG.error(f"{type(ex).__name__}: {str(ex)}")

    def restart(self):
        """
        Restarts the sensor manager. This is helpful when sensor calls start erroring out.
        """
        self.exit()
        self.__connect_to_database()
        self.dht = adafruit_dht.DHT22(self.__DHT_PIN)

    def __connect_to_database(self):
        """
        Connects to the database by initializing the db manager.
        """
        db_params = self.__get_databse_params()
        self.db = DBMgr(**db_params)

    def __get_databse_params(self) -> Dict[str, Any]:
        """
        Retrieves the databse information and credentials from the vault. These parameters are used
        to connect to the DB.

        Returns:
            Dict[str,Any]: The database parameters.
        """
        data = self.__vault.get_secret(f"{self.__VAULT_ROOT}database")
        connect_params = {
            "host": data["hostname"],
            "user": data["user"],
            "password": data["password"],
            "port": data["port"],
            "dbname": data["dbname"],
            "options": f"-c search_path={data['schema']}",
            "application_name": self.__class__.__name__,
        }
        return connect_params

    @staticmethod
    def __to_farenheit(celsius_temp: float) -> float:
        """
        Converts Celsius to Farenheit.

        Args:
            celsius_temp (float): The temperature in C.

        Returns:
            float: The temperature in F.
        """
        return (celsius_temp * 9 / 5) + 32

    def get_sensor_data(self) -> Dict[str, Any]:
        """
        Retrieves environment information from the sensors. This information is returned as a dict.

        Returns:
            Dict[str, Any]: The environment sensor data.
        """
        now = dt.datetime.now().replace(second=0, microsecond=0)
        _LOG.info("Getting environment data")
        humdity = self.dht.humidity
        temp = self.dht.temperature
        temp = self.__to_farenheit(temp)
        sensor_data = {
            "datetime": now,
            "temperature": temp,
            "humidity": humdity,
            "location": self.location,
        }
        threshold = constants.sensor_threshold[self.location]
        sensor_data["temp_critical"] = temp <= threshold["temp"][0] or temp >= threshold["temp"][1]
        sensor_data["humidity_critical"] = (
            humdity <= threshold["humidity"][0] or humdity >= threshold["humidity"][1]
        )
        _LOG.info("Current Enviroment Data:")
        log_dict(sensor_data)
        return sensor_data

    def update_db_sensor_data(self, sensor_data: Dict[str, Any]):
        """
        Updates the database with sensor data provided in the params.

        Args:
            sensor_data (Dict[str, Any]): The sensor data to add to the database

        Raises:
            ValueError: If the key columns location and datetime are not provided.
        """
        if not ("datetime" in sensor_data and "location" in sensor_data):
            raise ValueError("Missing primary key columns: location, datetime")
        self.db.insert_data(self.__SENSOR_TABLE, sensor_data)
