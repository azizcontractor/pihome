#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Useful logging functions for pihome
File: log
Project: PiHome
File Created: Tuesday, 26th October 2021 4:33:11 pm
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
import sys
from logging.handlers import RotatingFileHandler
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from pathlib import Path

__LOG = logging.getLogger(__name__)
__LOG_FORMAT = (
    "%(asctime)s %(levelname)8.8s %(name)20.20s %(threadName)10.10s %(lineno)04d > %(message)s"
)


def log_dict(dict_obj: dict, section_sep: str = "="):
    """
    Logs a dictionary in a key: value format. All keys are aligned properly when logging.

    Args:
        dict_obj (dict): The dictionary to log.
        section_sep (str, optional): The separator to use for the section. Defaults to "=".
    """
    __LOG.info(section_sep * 80)
    if dict_obj:
        max_len = max(len(str(key)) for key in dict_obj)
        for key, value in dict_obj.items():
            __LOG.info(f"   {key:{max_len}} : {value}")
    __LOG.info(section_sep * 80)


def get_logger(
    filepath: "Path",
    level: Union[int, str] = "INFO",
    max_size: int = 1024 ** 2,
    backup_count: int = 10,
) -> logging.Logger:
    """
    Initializes the root logger and sets a rotating file handler. If a terminal is present, this
    function also adds a streamhandler for the console.

    Args:
        filepath (Path): The path to the logfile
        level (Union[int, str], optional): The log level. Defaults to "INFO".
        max_size (int, optional): The maxe size in bytes for the log file. Defaults to 1024**2.
        backup_count (int, optional): The number of backup logs to keep. Defaults to 10.

    Returns:
        logging.Logger: The root logger.
    """
    log = logging.getLogger()
    log.setLevel(level)
    log.handlers = []
    fmt = logging.Formatter(__LOG_FORMAT)
    # file handler
    fhdlr = RotatingFileHandler(filepath, mode="w", maxBytes=max_size, backupCount=backup_count)
    fhdlr.setLevel(level)
    fhdlr.setFormatter(fmt)
    log.addHandler(fhdlr)
    if sys.stdout.isatty():
        chdlr = logging.StreamHandler()
        chdlr.setLevel("INFO")
        chdlr.setFormatter(fmt)
        log.addHandler(chdlr)
    return log
