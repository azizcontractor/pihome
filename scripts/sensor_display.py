#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Displays the sensor data on the OLED screen
File: sensor_display
Project: PiHome
File Created: Sunday, 28th November 2021 12:10:10 pm
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
from pathlib import Path
from typing import Any, Dict

import pihome.constants as constants
from pihome.i2cdisplay import Display
from pihome.log import get_logger
from pihome.shared import GracefulExit, connect_to_vault


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
        display = Display(vault, location)
        timeout = 0.5
        max_tries = 5
        while not exit_control.exit_now.wait(timeout=timeout):
            exit_proc = False
            now = dt.datetime.now()
            num_tries = 0
            while num_tries < max_tries:
                num_tries += 1
                try:
                    sensor_data = display.get_sensor_data()
                    display.display_sensor_data(sensor_data)
                except Exception as ex:
                    if num_tries < max_tries:
                        log.error(f"{type(ex).__name__}: {str(ex)}")
                    else:
                        log.exception(f"Could not fetch sensor data for {now}.")
                    exit_proc = exit_control.exit_now.wait(5)
                finally:
                    if exit_proc:
                        break
            if not exit_proc:
                now = dt.datetime.now()
                next_minute = (now + dt.timedelta(minutes=1)).replace(second=15, microsecond=0)
                timeout = (next_minute - now).total_seconds()
                log.debug(f"Waiting for next minute: {next_minute}")
        display.exit()
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
