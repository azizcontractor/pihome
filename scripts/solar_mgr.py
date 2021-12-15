#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Solar manager main script that runs as service for PiHome
File: solar
Project: scripts
File Created: Tuesday, 26th October 2021 5:11:23 pm
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
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any
import pihome.constants as constants
from pihome.log import get_logger
from pihome.solar import SolarMgr
from pihome.notify import NotifyMgr
from pihome.shared import GracefulExit, connect_to_vault


def check_status(previous_power: Dict[str, Any], current_power: Dict[str, Any], notify: NotifyMgr):
    if not previous_power:
        log.info("No previous power data to compare.")
        return
    if current_power["battery_critical"] and not previous_power["battery_critical"]:
        notify.notify(
            f"Battery status is critical. Please investigate.", "alert", Path(__file__).stem
        )
    keys = ["solar_status", "battery_status", "grid_status"]
    alerts_sent = False
    for key in keys:
        if current_power[key] != previous_power[key]:
            log.info(f"Sending alert {key}: {previous_power[key]} -> {current_power[key]}")
            notify.notify(
                f"{key.replace('_',' ').title()} switched from {previous_power[key]} to {current_power[key]}",
                "alert",
                Path(__file__).stem,
            )
            alerts_sent = True
    if not alerts_sent:
        log.debug("No alerts issued.")


def main() -> int:
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
        solar = SolarMgr(vault)
        notify = NotifyMgr(vault)
        data_updated = False
        timeout = 0.5
        max_tries = 3
        previous_power_data = {}
        while not exit_control.exit_now.wait(timeout=timeout):
            exit_proc = False
            now = dt.datetime.now()
            if now.minute % 10 == 1:
                num_tries = 0
                while not data_updated and num_tries < max_tries:
                    num_tries += 1
                    try:
                        energy_data = solar.get_energy()
                        power_data = solar.get_power()
                        solar.update_db_energy_data(energy_data)
                        solar.update_power_data(power_data)
                        data_updated = True
                        log.info(
                            f"Data updated for {now}. Sleeping until next data collection cycle."
                        )
                        check_status(previous_power_data, power_data, notify)
                        previous_power_data = power_data
                    except Exception as ex:
                        if num_tries < max_tries:
                            log.error(f"{type(ex).__name__}: {str(ex)}")
                        else:
                            log.exception(f"Could not fetch solar data for {now}.")
                        exit_proc = exit_control.exit_now.wait(10)
                    finally:
                        if exit_proc:
                            break
            else:
                data_updated = False
            if not exit_proc:
                now = dt.datetime.now()
                next_minute = (now + dt.timedelta(minutes=1)).replace(second=10, microsecond=0)
                timeout = (next_minute - now).total_seconds()
                log.debug(f"Waiting for next minute: {next_minute}")
        solar.exit()
        notify.exit()
        log.info(f"Exited at {now}")
    except Exception:
        _, _, exc_tb = sys.exc_info()
        exit_code = exc_tb.tb_lineno
        log.exception("Fatal Error")
    finally:
        return exit_code


if __name__ == "__main__":
    log_filepath = constants.log_dir / f"{Path(__file__).stem}.log"
    log = get_logger(log_filepath, level="DEBUG")
    sys.exit(main())
