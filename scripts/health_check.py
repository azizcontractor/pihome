#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Health check service script for PiHome
File: health_check
Project: PiHome
File Created: Wednesday, 17th November 2021 5:04:37 pm
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
from pihome.health import HealthMgr
from pihome.shared import GracefulExit, connect_to_vault
from pihome.notify import NotifyMgr
from typing import Dict, Any


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
        health = HealthMgr(vault)
        notify = NotifyMgr(vault)
        data_updated = False
        timeout = 0.5
        max_tries = 5
        cpu_temp_last_alert = None
        cpu_usage_last_alert = None
        mem_usage_last_alert = None
        disk_usage_last_alert = None
        while not exit_control.exit_now.wait(timeout=timeout):
            exit_proc = False
            now = dt.datetime.now()
            if now.minute % 5 == 0:
                num_tries = 0
                while not data_updated and num_tries < max_tries:
                    num_tries += 1
                    try:
                        stats = health.get_stats()
                        cpu_temp_critical = stats.pop("cpu_temp_critical")
                        cpu_usage_critical = stats.pop("cpu_usage_critical")
                        mem_usage_critical = stats.pop("mem_usage_critical")
                        disk_usage_critical = stats.pop("disk_usage_critical")
                        nodename = stats["nodename"]
                        health.update_db_system_stats(stats)
                        data_updated = True
                        log.info(
                            f"Data updated for {now}. Sleeping until next data collection cycle."
                        )
                        if cpu_temp_critical and (
                            cpu_temp_last_alert is None
                            or dt.datetime.now() >= dt.timedelta(minutes=60) + cpu_temp_last_alert
                        ):
                            notify.notify(
                                f"{nodename} CPU temperature critical at "
                                f"{stats['cpu_temp']}\u00b0C.",
                                "critical",
                                Path(__file__).stem,
                            )
                            cpu_temp_last_alert = dt.datetime.now()
                        if cpu_usage_critical and (
                            cpu_usage_last_alert is None
                            or dt.datetime.now() >= dt.timedelta(minutes=60) + cpu_usage_last_alert
                        ):
                            notify.notify(
                                f"{nodename} CPU Usage critical at {stats['cpu_usage']}%.",
                                "critical",
                                Path(__file__).stem,
                            )
                            cpu_usage_last_alert = dt.datetime.now()
                        if mem_usage_critical and (
                            mem_usage_last_alert is None
                            or dt.datetime.now() >= dt.timedelta(minutes=60) + mem_usage_last_alert
                        ):
                            notify.notify(
                                f"{nodename} Memory Usage critical at {stats['mem_usage']}%.",
                                "critical",
                                Path(__file__).stem,
                            )
                            mem_usage_last_alert = dt.datetime.now()
                        if disk_usage_critical and (
                            disk_usage_last_alert is None
                            or dt.datetime.now() >= dt.timedelta(minutes=60) + disk_usage_last_alert
                        ):
                            notify.notify(
                                f"{nodename} Disk Usage critical at "
                                f"{round((stats['disk_usage']/stats['disk_total'])*100,2)}%.",
                                "critical",
                                Path(__file__).stem,
                            )
                            mem_usage_last_alert = dt.datetime.now()

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
        health.exit()
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
