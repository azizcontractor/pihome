#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Solar manager for pihome
File: solar_mgr
Project: PiHome
File Created: Tuesday, 26th October 2021 11:41:45 am
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

import pihome.constants as constants
import solaredge
from pihome.log import log_dict
from pihome.db import DBMgr

if TYPE_CHECKING:
    from pihome.vault import VaultMgr

_LOG = logging.getLogger(__name__)


class SolarMgr:
    """
    This class manages gathering data from the solaredge API and adding it to a database. The data
    is gathered using the solaredge python module to call functions against the solaredge REST
    API interface. Once the data is collected it is returned in a dictionary format where the
    keys are table columns in the DB.

    Attributes:
        solar (solaredge.Solaredge): The solaredge module to query solaredge.
        db (DBMgr): The database module to add data to the DB.
    """

    __TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    __VAULT_ROOT = "solar/"
    __METERS = {
        "Purchased": "import",
        "FeedIn": "export",
        "Consumption": "consumption",
        "SelfConsumption": "self_consumption",
        "Production": "production",
    }
    __ENERGY_TABLE = "energy"
    __POWER_TABLE = "power"

    def __init__(self, vault: "VaultMgr") -> None:
        """
        Initializes the solar manager. Connects to the database and the solaredge API during the
        initialization process.

        Args:
            vault (VaultMgr): The vault to read secrets from.
        """
        _LOG.info(f"Initializing Solar Manager")
        self.__vault = vault
        data = self.__get_solaredge_credentials()
        self.__site_id = data["site_id"]
        self.__api_key = data["api_key"]
        self.__connect_to_solaredge()
        self.__connect_to_database()

    def exit(self):
        """
        Exits the solar manager. Calls the DB exit method to close DB connection.
        """
        self.db.exit()

    def __connect_to_solaredge(self):
        """
        Connects to the solaredge site API.
        """
        self.solar = solaredge.Solaredge(self.__api_key)

    def __connect_to_database(self):
        """
        Connects to the database by initializing the DB manager.
        """
        db_params = self.__get_databse_params()
        self.db = DBMgr(**db_params)

    def __get_solaredge_credentials(self) -> Dict[str, Any]:
        """
        Gets the solaredge credentials from the vault.

        Returns:
            Dict[str, Any]: The dict containing solaredge credentials.
        """
        return self.__vault.get_secret(f"{self.__VAULT_ROOT}solaredge")

    def __get_databse_params(self) -> Dict[str, Any]:
        """
        Gets the database connection params from the vault.

        Returns:
            Dict[str, Any]: The DB connection params.
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

    def get_energy(self) -> Dict[str, Any]:
        """
        Gets energy data from solaredge and returns it as a dictionary.

        Returns:
            Dict[str, Any]: The energy data from solaredge.
        """
        _LOG.info(f"Getting today's energy data for {self.__site_id}")
        end = dt.datetime.now()
        start = dt.datetime.combine(dt.date.today(), dt.time(0, 0, 0))
        _LOG.info(f"Getting energy details for {self.__site_id}")
        data = self.solar.get_energy_details(
            self.__site_id, start.strftime(self.__TIME_FORMAT), end.strftime(self.__TIME_FORMAT)
        )
        _LOG.debug(data)
        energy_data = {"date": start.date()}
        for meter_data in data["energyDetails"]["meters"]:
            meter_type = meter_data["type"]
            energy_values = meter_data.get("values", [])
            energy = energy_values[0].get("value", 0)
            energy_data[self.__METERS[meter_type]] = energy
        _LOG.info("Energy Data:")
        log_dict(energy_data)
        return energy_data

    def get_power(self) -> Dict[str, Any]:
        """
        Gets the current power data from solar edge and returns it as dict.

        Returns:
            Dict[str, Any]: The current power data from solaredge.
        """
        _LOG.info(f"Getting power data for {self.__site_id}")
        data = self.solar.get_current_power_flow(self.__site_id)
        _LOG.debug(data)
        now = dt.datetime.now()
        power_data = {
            "datetime": now.replace(second=0, microsecond=0),
            "grid_status": data["siteCurrentPowerFlow"]["GRID"]["status"],
            "grid_power": data["siteCurrentPowerFlow"]["GRID"]["currentPower"],
            "solar_status": data["siteCurrentPowerFlow"]["PV"]["status"],
            "solar_power": data["siteCurrentPowerFlow"]["PV"]["currentPower"],
            "battery_status": data["siteCurrentPowerFlow"]["STORAGE"]["status"],
            "battery_power": data["siteCurrentPowerFlow"]["STORAGE"]["currentPower"],
            "battery_charge": data["siteCurrentPowerFlow"]["STORAGE"]["chargeLevel"],
            "battery_critical": data["siteCurrentPowerFlow"]["STORAGE"]["critical"],
            "power_usage": data["siteCurrentPowerFlow"]["LOAD"]["currentPower"],
        }
        _LOG.info("Power Data:")
        log_dict(power_data)
        return power_data

    def update_db_energy_data(self, energy_data: Dict[str, Any]):
        """
        Updates the database with the given energy data.

        Args:
            energy_data (Dict[str, Any]): The energy data to upload to the DB.

        Raises:
            ValueError: If the primary key date column is not present in the data.
        """
        if "date" not in energy_data:
            raise ValueError(f"Missing primary key column datetime.")
        self.db.insert_or_update_data(self.__ENERGY_TABLE, energy_data, ["date"])

    def update_power_data(self, power_data: Dict[str, Any]):
        """
        Uploads the given power data to the database.

        Args:
            power_data (Dict[str, Any]): The power data to add to the DB.

        Raises:
            ValueError: If the primary key datetime column is not present in the data dict.
        """
        if "datetime" not in power_data:
            raise ValueError(f"Missing primary key column datetime.")
        self.db.insert_data(self.__POWER_TABLE, power_data, ["datetime"])
