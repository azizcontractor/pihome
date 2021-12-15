#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
OLED Display controller script for PiHome
File: i2cdisplay
Project: PiHome
File Created: Sunday, 28th November 2021 9:24:47 am
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




import datetime as dt
import logging
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from pihome.vault import VaultMgr

import adafruit_ssd1306
import board
import digitalio
from PIL import Image, ImageDraw, ImageFont

import pihome.constants as constants
from pihome.db import DBMgr
from pihome.log import log_dict

_LOG = logging.getLogger(__name__)


class Display:

    WIDTH = 128
    HEIGHT = 16
    ADDR = 0x3C
    COLOR_BIT = "1"
    FONT = ImageFont.truetype("PixelOperator", 16)
    __VAULT_ROOT = "sensor/"
    __SENSOR_TABLE = "environment"
    __AVAIL_LOCATIONS = ["upstairs", "downstairs", "attic"]

    def __init__(self, vault: "VaultMgr", location: str) -> None:
        if location not in self.__AVAIL_LOCATIONS:
            raise ValueError(
                f"Invalid location {location}. Must be one of {self.__AVAIL_LOCATIONS}"
            )
        _LOG.info("Initializing I2C Display Manager.")
        self.oled_reset = digitalio.DigitalInOut(board.D4)
        self.i2c = board.I2C()
        self.oled = adafruit_ssd1306.SSD1306_I2C(
            self.WIDTH, self.HEIGHT, self.i2c, addr=self.ADDR, reset=self.oled_reset
        )
        self.clear_display()
        self.location = location
        self.__vault = vault
        self.__connect_to_database()

    def clear_display(self):
        _LOG.info("Clearing Display")
        self.oled.fill(0)
        self.oled.show()

    def exit(self):
        """
        Exits the sensor manager. Calls the DB exit method to close DB connection.
        """
        self.db.exit()
        self.clear_display()

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

    def get_sensor_data(self) -> Dict[str, Any]:
        """
        Fetches the latest sensor data from the db

        Raises:
            Exception: If no data is found for today's date.

        Returns:
            Dict[str,Any]: The sensor data: temperature, humidity, location
        """
        sql = (
            f"SELECT MAX(datetime) FROM {self.__SENSOR_TABLE} "
            "WHERE DATE(datetime) = %s AND location = %s"
        )
        params = [dt.date.today(), self.location]
        _LOG.info(f"Fetching latest sensor update for today {dt.date.today()}")
        row = self.db.fetch_raw(sql, params, single_row=True)
        if not row:
            raise Exception(f"Could not fetch data for {dt.date.today()}")
        max_datetime = row[0]
        _LOG.info(f"Latest sensor update: {max_datetime}")
        row = self.db.fetch_data(
            self.__SENSOR_TABLE,
            ["temperature", "humidity", "location"],
            {"datetime": max_datetime, "location": self.location},
            single_row=True,
        )
        data = {"temperature": row[0], "humidity": row[1], "location": row[2]}
        _LOG.info("Fetched Data:")
        log_dict(data)
        return data

    def display_sensor_data(self, data: Dict[str, Any]):
        """
        Shows the sensor data on the OLED screen.

        Args:
            data (Dict[str, Any]): The data to display
        """
        self.clear_display()
        image = Image.new(self.COLOR_BIT, (self.oled.width, self.oled.height))
        draw = ImageDraw.Draw(image)
        oled_str = (
            f"{data['location'].title()[:9]}: "
            f"{int(round(data['temperature'],0))}\u00b0C {int(round(data['humidity'],0))}%"
        )
        draw.text((0, 0), oled_str, font=self.FONT, fill=255)
        _LOG.info(f"Showing stats: {oled_str}")
        self.oled.image(image)
        self.oled.show()
