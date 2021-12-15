#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
XDB Manager script for PiHome
File: xdb
Project: PiHome
File Created: Wednesday, 17th November 2021 5:55:21 pm
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
import sys
from pathlib import Path
from typing import Any, Dict

import pihome.constants as constants
from pihome.db import DBMgr
from pihome.log import get_logger
from pihome.shared import GracefulExit, connect_to_vault, load_json_data


def update_db_with_xdb(xdb_path: Path, db_data: Dict[str, Any]):
    connect_params = {
        "host": db_data["hostname"],
        "user": db_data["user"],
        "password": db_data["password"],
        "port": db_data["port"],
    }
    xdb_data = load_json_data(xdb_path)
    options = xdb_data["dboptions"]
    kwargs = xdb_data["dbkwargs"]
    connect_params["dbname"] = xdb_data["dbname"]
    if options is not None:
        connect_params["options"] = options
    if kwargs:
        connect_params.update(kwargs)
    db = DBMgr(**connect_params)
    dispatch = {
        "insert": db.insert_data,
        "update": db.update_data,
        "insert_update": db.insert_or_update_data,
        "delete": db.delete_data,
    }
    dispatch[xdb_data["txn_type"]](**xdb_data["kwargs"], update_xdb=False)
    xdb_path.unlink()


def main():
    try:
        exit_code = 0
        exit_control = GracefulExit()
        vault = None
        attempts = 0
        log.info(f"Attempting to connect to vault.")
        timeout = 0.5
        while vault is None and not exit_control.exit_now.wait(timeout=timeout):
            vault = connect_to_vault()
            attempts += 1
            if vault is None:
                log.info(f"Connection failed (total attempts={attempts}). Retrying...")
            if vault is None:
                timeout = 10
        if exit_control.exit_now.is_set():
            log.info("Exit signal recieved. Exiting...")
            exit_code = 255
            return
        log.info(f"Connected to vault after {attempts} attempt(s).")
        db_data = vault.get_secret("xdb/database")
        while not exit_control.exit_now.wait(timeout=timeout):
            now = dt.datetime.now()
            if now.minute % 5 == 0:
                try:
                    for fp in constants.data_dir.glob("*.xdb"):
                        log.info(f"File found: {fp}")
                        update_db_with_xdb(fp, db_data)
                except Exception as ex:
                    log.error(f"{type(ex).__name__}: {str(ex)}")
                    log.error("Could not update DB will try again in 5 minutes.")
            now = dt.datetime.now()
            next_minute = (now + dt.timedelta(minutes=1)).replace(second=10, microsecond=0)
            timeout = (next_minute - now).total_seconds()
            log.debug(f"Waiting for next minute: {next_minute}")
    except:
        _, _, exc_tb = sys.exc_info()
        exit_code = exc_tb.tb_lineno
        log.exception("Fatal Error")
    finally:
        return exit_code


if __name__ == "__main__":
    log_filepath = constants.log_dir / f"{Path(__file__).stem}.log"
    log = get_logger(log_filepath, level="DEBUG")
    sys.exit(main())
