#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Script to unseal the vault. Executed at boot via cron.
File: vault_unseal
Project: scripts
File Created: Tuesday, 26th October 2021 1:46:51 pm
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
import socket
import sys
import time

import pihome.constants as constants
import requests
from pihome.log import get_logger, log_dict

VAULT_KEY_NAME = "VAULT_UNSEAL_KEY"


def wait_for_port(port, host="localhost", timeout=5.0):
    """Wait until a port starts accepting TCP connections.
    Args:
        port (int): Port number.
        host (str): Host address on which the port should exist.
        timeout (float): In seconds. How long to wait before raising errors.
    Raises:
        TimeoutError: The port isn't accepting connection after time specified in `timeout`.
    """
    start_time = time.perf_counter()
    while True:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                break
        except OSError as ex:
            time.sleep(0.01)
            if time.perf_counter() - start_time >= timeout:
                raise TimeoutError(
                    "Waited too long for the port {} on host {} to start accepting "
                    "connections.".format(port, host)
                ) from ex


def main():
    try:
        exit_code = 0
        wait_for_port(os.getenv("VAULT_PORT"))
        unseal_url = f"{os.getenv('VAULT_ADDR')}/v1/sys/unseal"
        status_url = f"{os.getenv('VAULT_ADDR')}/v1/sys/seal-status"
        resp = requests.get(status_url)
        if "sealed" not in resp.json():
            raise Exception(f"Could not determine seal status of vault")
        if "t" not in resp.json():
            raise Exception(f"Could not determine unseal threshold.")
        threshold = resp.json()["t"]
        log.info(f"Vault Sealed: {resp.json()['sealed']}")
        log_dict(resp.json())
        if resp.json()["sealed"]:
            for i in range(threshold):
                unseal_key = os.getenv(f"{VAULT_KEY_NAME}{i+1}")
                resp = requests.put(unseal_url, json={"key": unseal_key})
                log.info(f"Unseal {i+1} response:")
                log_dict(resp.json())
        resp = requests.get(status_url)
        if "sealed" not in resp.json():
            raise Exception(f"Could not determine seal status of vault")
        log.info(f"Vault Sealed: {resp.json()['sealed']}")
        log_dict(resp.json())
        if resp.json()["sealed"]:
            raise Exception("Failed to unseal vault.")
    except:
        _, _, exc_tb = sys.exc_info()
        exit_code = exc_tb.tb_lineno
        log.exception("FATAL ERROR")
    finally:
        return exit_code


if __name__ == "__main__":
    log_filepath = (
        constants.log_dir / f"vault_unseal_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    log = get_logger(log_filepath, backup_count=0)
    sys.exit(main())
