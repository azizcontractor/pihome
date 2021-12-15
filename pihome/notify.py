#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Notification manager for PiHome
File: notify
Project: PiHome
File Created: Friday, 5th November 2021 7:59:03 pm
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
import socket
from typing import TYPE_CHECKING, Any, Dict

import requests

from pihome.db import DBMgr
from pihome.vault import VaultMgr

_LOG = logging.getLogger(__name__)


class NotifyMgr:
    __VAULT_ROOT = "report/"
    __NOTIFICATION_TABLE = "notifications"

    def __init__(self, vault: VaultMgr) -> None:
        _LOG.info("Initializing notification manager.")
        self.__vault = vault
        self.__connect_to_database()
        self.__get_pushed_credentials()

    def notify(self, msg: str, notif_type: str, app: str, node: str = None, push=True):
        now = dt.datetime.now()
        if node is None:
            node = socket.gethostname()
        data = {
            "msg": msg,
            "node": node,
            "datetime": now,
            "type": notif_type,
            "app": app,
            "status": "unread",
        }
        if push:
            data["pushed"] = self.push_notify(msg, app, node)
        else:
            data["pushed"] = False
        self.db.insert_data(self.__NOTIFICATION_TABLE, data)

    def exit(self):
        """
        Exits the notify manager. Calls the DB exit method to close DB connection.
        """
        self.db.exit()

    def push_notify(self, msg: str, app: str, node: str) -> bool:
        """
        Sends a push notification using the pushed API.

        Args:
            msg (str): The messag to send.
            app (str): The app sending the message
            node (str): The node sending the notification.

        Returns:
            bool: True if successful False otehrwise
        """
        content = f"{node}.{app} -> {msg}"
        try:
            payload = payload = {
                "app_key": self.__pushed_key,
                "app_secret": self.__pushed_secret,
                "target_type": "app",
                "content": content,
            }
            resp = requests.post(self.__pushed_url, data=payload)
            resp.raise_for_status()
            _LOG.info(resp.text)
            success = True
        except Exception as ex:
            _LOG.exception("Push Notify Error")
            success = False
        finally:
            return success

    def __get_pushed_credentials(self):
        """
        Sets the credentials for connecting to pushed API
        """
        data = self.__vault.get_secret(f"{self.__VAULT_ROOT}pushed")
        self.__pushed_key = data["app_key"]
        self.__pushed_secret = data["app_secret"]
        self.__pushed_url = data["url"]

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


if __name__ == "__main__":
    import os

    from dotenv import load_dotenv

    import pihome.constants as constants

    logging.basicConfig(level="INFO", format="%(asctime)s > %(message)s")

    load_dotenv(dotenv_path=constants.env_dir / "datanode.env")
    vault = VaultMgr(os.getenv("VAULT_URL"), os.getenv("ROLE_ID"), os.getenv("SECRET_ID"))
    notify = NotifyMgr(vault)
    notify.notify("This is a test notification", "alert", "test")
