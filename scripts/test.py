#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
This is a test script for test code
File: test
Project: pihome
File Created: Monday, 25th October 2021 6:22:15 pm
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
import logging

logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s > %(message)s")
log = logging.getLogger()

import datetime as dt

###################################solar###########################################################

# import solaredge
# api_key = "MGP7EQPNNCW5PS8FV1EH3EODDD152T7E"
# site_id = "2477668"

# s = solaredge.Solaredge(api_key)

# resp = s.get_energy_details(
#     site_id,
#     dt.datetime.combine(dt.date.today(), dt.time(0, 0, 0)).strftime("%Y-%m-%d %H:%M:%S"),
#     dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
# )
# log.info(resp)

# resp = s.get_energy(
#     site_id, dt.date.today().strftime("%Y-%m-%d"), dt.date.today().strftime("%Y-%m-%d")
# )
# log.info(resp)

# resp = s.get_current_power_flow(site_id)
# log.info(resp)


####################################Vault##########################################################

# from pihome.vault_mgr import VaultMgr

# vault = VaultMgr(
#     "http://192.168.50.77:8200",
#     "49662e3e-9d83-adb4-198b-dd6e9d00b9ac",
#     "29d58d84-f638-6c85-8851-ca9544fd918c",
# )
# secrets = vault.list_secrets("solar")
# log.info(secrets)
# secret = vault.get_secret("solar/solaredge")
# log.info(secret)

###################################database########################################################

from pihome.db import DBMgr
from pihome.vault import VaultMgr

vault = VaultMgr(
    "http://192.168.50.77:8200",
    "49662e3e-9d83-adb4-198b-dd6e9d00b9ac",
    "29d58d84-f638-6c85-8851-ca9544fd918c",
)
data = vault.get_secret("solar/database")

connect_params = {
    "host": data["hostip"],
    "user": data["user"],
    "password": data["password"],
    "port": data["port"],
    "dbname": data["dbname"],
    "options": f"-c search_path={data['schema']}",
}

db = DBMgr(**connect_params)
db.delete_data("energy")
db.delete_data("power")
