#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Sensor manager main script that runs as service for PiHome.
File: sensor_mgr
Project: PiHome
File Created: Friday, 29th October 2021 8:04:32 pm
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

import pihome.constants as constants
from pihome.log import get_logger
from pihome.sensor import SensorMgr
from pihome.shared import GracefulExit, connect_to_vault
from pihome.notify import NotifyMgr


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
        location = os.getenv("LOCATION")
        sensor = SensorMgr(vault, location)
        notify = NotifyMgr(vault)
        data_updated = False
        timeout = 0.5
        max_tries = 5
        temp_last_alert = None
        humidity_last_alert = None
        while not exit_control.exit_now.wait(timeout=timeout):
            exit_proc = False
            now = dt.datetime.now()
            if now.minute % 3 == 0:
                num_tries = 0
                while not data_updated and num_tries < max_tries:
                    num_tries += 1
                    try:
                        if num_tries > 2:
                            sensor.restart()
                        sensor_data = sensor.get_sensor_data()
                        temp_critical = sensor_data.pop("temp_critical")
                        humidity_critical = sensor_data.pop("humidity_critical")
                        sensor.update_db_sensor_data(sensor_data)
                        data_updated = True
                        log.info(
                            f"Data updated for {now}. Sleeping until next data collection cycle."
                        )
                        if temp_critical and (
                            temp_last_alert is None
                            or dt.datetime.now() >= temp_last_alert + dt.timedelta(minutes=60)
                        ):
                            notify.notify(
                                f"{location.title()} temperature critical at "
                                f"{sensor_data['temperature']}\u00b0F.",
                                "alert",
                                Path(__file__).stem,
                            )
                            temp_last_alert = dt.datetime.now()
                        if humidity_critical and (
                            humidity_last_alert is None
                            or dt.datetime.now() >= humidity_last_alert + dt.timedelta(minutes=60)
                        ):
                            notify.notify(
                                f"{location.title()} humidity critical at "
                                f"{sensor_data['humidity']}%.",
                                "alert",
                                Path(__file__).stem,
                            )
                            humidity_last_alert = dt.datetime.now()
                    except Exception as ex:
                        if num_tries < max_tries:
                            log.error(f"{type(ex).__name__}: {str(ex)}")
                        else:
                            log.exception(f"Could not fetch sensor data for {now}.")
                        exit_proc = exit_control.exit_now.wait(5)
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
        sensor.exit()
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
