#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Health check module for PiHome
File: health
Project: PiHome
File Created: Wednesday, 17th November 2021 4:01:24 pm
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
import shutil
import socket
import time
from typing import TYPE_CHECKING, Any, Dict

import psutil
from dotenv import dotenv_values
from gpiozero import CPUTemperature

import pihome.constants as constants
from pihome.db import DBMgr
from pihome.log import log_dict
from pihome.vault import VaultMgr

_LOG = logging.getLogger(__name__)


class HealthMgr:
    __VAULT_ROOT = "report/"
    __STAT_TABLE = "system_stats"
    __CPU_TEMP_MAX = 65
    __CPU_USAGE_MAX = 70
    __MEM_USAGE_MAX = 70
    __DISK_USAGE_MAX = 90

    def __init__(self, vault: VaultMgr) -> None:
        _LOG.info("Initializing health monitor.")
        self.__vault = vault
        self.__connect_to_database()

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

    def exit(self):
        """
        Exits the health manager. Calls the DB exit method to close DB connection.
        """
        self.db.exit()

    def get_stats(self) -> Dict[str, Any]:
        """
        Fetches the system stats like cpu percent, memory percent, disk usage, and cpu temperature.

        Returns:
            Dict[str, Any]: The stats fetched from the system
        """
        cpu = CPUTemperature()
        disk_data = shutil.disk_usage("/")
        uptime_str = get_uptime()
        stats = {
            "cpu_temp": cpu.temperature,
            "nodename": socket.gethostname(),
            "cpu_usage": psutil.cpu_percent(),
            "mem_usage": psutil.virtual_memory().percent,
            "datetime": dt.datetime.now(),
            "disk_usage": disk_data.used,
            "disk_total": disk_data.total,
            "uptime": uptime_str,
        }
        stats["cpu_temp_critical"] = stats["cpu_temp"] >= self.__CPU_TEMP_MAX
        stats["cpu_usage_critical"] = stats["cpu_usage"] >= self.__CPU_USAGE_MAX
        stats["mem_usage_critical"] = stats["mem_usage"] >= self.__MEM_USAGE_MAX
        stats["disk_usage_critical"] = (
            stats["disk_usage"] / stats["disk_total"] >= self.__DISK_USAGE_MAX
        )
        if "sensor" in stats["nodename"]:
            env_file = constants.env_dir / "sensornode.env"
            env_values = dotenv_values(dotenv_path=env_file)
            stats["location"] = env_values["LOCATION"]
        _LOG.info("Current System Stats")
        log_dict(stats)
        return stats

    def update_db_system_stats(self, stats: Dict[str, Any]):
        """
        Adds the supplied system stats to the database

        Args:
            stats (Dict[str, Any]): The stats to add to the database

        Raises:
            ValueError: If the primary key columns nodename and datetime are missing.
        """
        if not ("datetime" in stats and "nodename" in stats):
            raise ValueError("Missing primary key columns: nodename, datetime")
        self.db.insert_data(self.__STAT_TABLE, stats)


def get_uptime() -> str:
    uptime = time.time() - psutil.boot_time()
    uptime_str = "UP "
    if uptime > 86400:
        days, uptime = divmod(uptime, 86400)
        uptime_str += f"{int(round(days))} Days, "
    if uptime > 3600:
        hours, uptime = divmod(uptime, 3600)
        uptime_str += f"{int(round(hours))}:"
    else:
        uptime_str += f"0:"
    if uptime > 60:
        minutes, uptime = divmod(uptime, 60)
        uptime_str += f"{int(round(minutes)):02d}:"
    else:
        uptime_str += f"00:"
    uptime_str += f"{int(round(uptime)):02d}"
    return uptime_str.strip()
