#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
%reload_ext autoreload
%autoreload 2
Shared classes and functions for pihome
File: graceful_exit
Project: PiHome
File Created: Wednesday, 27th October 2021 9:54:31 am
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
import json
import logging
import os
import shutil
import signal
import threading
from pathlib import Path
from typing import Union

from pihome.vault import VaultMgr

_LOG = logging.getLogger(__name__)


class GracefulExit:
    """
    Allows gracefully exiting a loop when SIGINT or SIGTERM is recieved.

    Attrs:
        exit_code (int): The flag indicating the signal that was recieved.
    """

    exit_now = threading.Event()

    def __init__(self) -> None:
        """
        Initializes the exit control object
        """
        signal.signal(signal.SIGINT, self.graceful_exit)
        signal.signal(signal.SIGTERM, self.graceful_exit)

    def graceful_exit(self, signum: int, frame):
        """
        Handler for sigterm and sigint signals. Sets the exit_code variable that can be referenced
        by callers.

        Args:
            signum (int): The exit signal recieved.
            frame: The stack frame.
        """
        self.exit_now.set()


def load_json_data(fpath: Path) -> Union[list, dict]:
    """
    Loads a JSON file and returns data.

    Args:
        fpath (Path): The path to the file

    Returns:
        Union[list, dict]: The data loaded from JSON.
    """
    with open(fpath) as f:
        data = json.load(f)
    return data


def write_json_data(fpath: Path, data: Union[list, dict], stage: bool = False):
    """
    Writes json data to file. If data contains non JSON serializable objects. It write their string
    representation to the file.

    Args:
        fpath (Path): The path to the file.
        data (Union[list, dict]): The data to write to the file.
    """
    if stage:
        final_fpath = fpath
        fpath = Path("/tmp") / fpath.name
    with open(fpath, "w") as f:
        json.dump(data, f, default=str)
    if stage:
        shutil.move(fpath, final_fpath)


def connect_to_vault() -> VaultMgr:
    """
    Connects to the vault using environment variables. The required env vars must be set prior to
    calling this function.

    Raises:
        ValueError: If required env vars are not set.

    Returns:
        VaultMgr: The vault manager to handle secrets.
    """
    VAULT_ENV_VARS = ["VAULT_URL", "ROLE_ID", "SECRET_ID"]
    for env_var in VAULT_ENV_VARS:
        if os.getenv(env_var) is None:
            raise ValueError(f"ENV VAR {env_var} is not set.")
    try:
        vault = VaultMgr(os.getenv("VAULT_URL"), os.getenv("ROLE_ID"), os.getenv("SECRET_ID"))
    except Exception as ex:
        _LOG.error(f"Vault Connection Error. {type(ex).__name__}: {str(ex)}")
        vault = None
    finally:
        return vault
