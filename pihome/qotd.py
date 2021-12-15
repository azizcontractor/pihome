#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Quote of the day mgr for PiHome
File: qotd
Project: PiHome
File Created: Monday, 8th November 2021 4:15:36 pm
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
from pihome.log import log_dict

import requests

from pihome.db import DBMgr

if TYPE_CHECKING:
    from pihome.vault import VaultMgr

_LOG = logging.getLogger(__name__)


class QOTDMgr:
    __QUOTE_URL = "https://quotes.rest/qod.json"
    __QUOTE_TABLE = "qotd"
    __VAULT_ROOT = "quote/"

    def __init__(self, vault: "VaultMgr"):
        _LOG.info("Initializing Quote Manager")
        self.__vault = vault
        self.__connect_to_database()

    def exit(self):
        """
        Exits the sensor manager. Calls the DB exit method to close DB connection.
        """
        self.db.exit()

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

    def get_quote(self) -> Dict[str, Any]:
        """
        Fetches a new quote for quotes.rest and parses the data

        Raises:
            Exception: If response from API url is not 200 or if quote data cannot be parsed.

        Returns:
            Dict[str, Any]: The quote data containing quote, author, and title.
        """
        _LOG.info("Fetching new quote")
        resp = requests.get(self.__QUOTE_URL, timeout=10)
        if resp.status_code == 429:
            raise Exception(
                f"Error: {resp.json().get('error',{}).get('message','Too many requests')}"
            )
        resp.raise_for_status()
        resp_json = resp.json()
        data = resp_json.get("contents", {}).get("quotes", [None])[0]
        if data is None:
            raise Exception(f"Could not fetch quote. Invalid data {resp_json}.")
        quote_data = {
            "quote": data["quote"],
            "author": data["author"],
            "title": data["title"],
            "datetime": dt.datetime.now(),
        }
        _LOG.debug(data)
        _LOG.info("Fetched quote:")
        log_dict(quote_data)
        return quote_data

    def update_db_with_quote(self, quote_data: Dict[str, Any]):
        """
        Inserts the given quote data into the database. If the quote exists then it will not be
        added again.

        Args:
            quote_data (Dict[str, Any]): The quote data to be added.
        """
        with self.db.conn.cursor() as c:
            c.execute(
                f"SELECT * FROM {self.__QUOTE_TABLE} WHERE quote=%s AND DATE(datetime) = %s",
                (quote_data["quote"], quote_data["datetime"].date()),
            )
            rows = c.fetchall()
        if rows:
            _LOG.info("DB Update not required. Quote exists in DB for today's date.")
        else:
            self.db.insert_data(self.__QUOTE_TABLE, quote_data)


if __name__ == "__main__":
    logging.basicConfig(level="DEBUG")
    from pihome.vault import VaultMgr

    vault = VaultMgr(
        "http://192.168.50.77:8200",
        "49662e3e-9d83-adb4-198b-dd6e9d00b9ac",
        "29d58d84-f638-6c85-8851-ca9544fd918c",
    )
    qotd = QOTDMgr(vault)
    qd = qotd.get_quote()
    qotd.update_db_with_quote(qd)
