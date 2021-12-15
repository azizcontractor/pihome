#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Controls the display node and displays relevant data
File: display_controller
Project: PiHome
File Created: Friday, 5th November 2021 1:49:02 pm
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
import os
import subprocess
import sys
import time
from threading import Timer

import flask
import pihome.constants as constants
import pyautogui
from dotenv import load_dotenv
from flask import cli, jsonify, request
from pihome.log import get_logger, log_dict
from pihome.vault import VaultMgr
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait

FLASK_APP = flask.Flask("display-controller")


@FLASK_APP.route("/show/info", methods=["GET"])
def show_info():
    try:
        remote_host = request.remote_addr
        log.info(f"Request to show information from {remote_host}")
        driver.get(constants.piinfo_url)
        global notify_shown
        notify_shown = False
        response = {"success": True, "notifications_displayed": notify_shown}
    except Exception as ex:
        log.exception("Error showing info")
        response = {"success": False, "error": str(ex), "err_type": type(ex).__name__}
    finally:
        return jsonify(response)


@FLASK_APP.route("/show/slides", methods=["GET"])
def show_slides():
    try:
        remote_host = request.remote_addr
        log.info(f"Request to start slideshow from {remote_host}")
        driver.get(constants.piframe_url)
        global notify_shown
        notify_shown = False
        response = {"success": True, "notifications_displayed": notify_shown}
    except Exception as ex:
        log.exception("Error showing slideshow")
        response = {"success": False, "error": str(ex), "err_type": type(ex).__name__}
    finally:
        return jsonify(response)


@FLASK_APP.route("/show/system", methods=["GET"])
def show_system():
    try:
        remote_host = request.remote_addr
        log.info(f"Request to start slideshow from {remote_host}")
        driver.get(constants.pihome_base_url)
        global notify_shown
        notify_shown = False
        response = {"success": True, "notifications_displayed": notify_shown}
    except Exception as ex:
        log.exception("Error showing slideshow")
        response = {"success": False, "error": str(ex), "err_type": type(ex).__name__}
    finally:
        return jsonify(response)


@FLASK_APP.route("/clear/notifications", methods=["GET"])
def clear_notifications():
    try:
        global notify_shown
        if not notify_shown:
            raise ValueError("Notifications not displayed.")
        remote_host = request.remote_addr
        log.info(f"Request to clear notifications from {remote_host}")
        driver.find_element_by_id("mark_all").click()
        pyautogui.FAILSAFE = False
        ycord = pyautogui.size()[0]
        pyautogui.moveTo(0, ycord)
        notify_shown = False
        response = {"success": True, "notifications_displayed": notify_shown}
    except Exception as ex:
        log.exception("Error clearing notifications")
        response = {"success": False, "error": str(ex), "err_type": type(ex).__name__}
    finally:
        return jsonify(response)


@FLASK_APP.route("/toggle/notifications", methods=["GET"])
def toggle_notifications():
    try:
        global notify_shown
        remote_host = request.remote_addr
        log.info(f"Request to toggle notifications from {remote_host}")
        driver.find_element_by_id("notify_alarm").click()
        pyautogui.FAILSAFE = False
        ycord = pyautogui.size()[0]
        pyautogui.moveTo(0, ycord)
        notify_shown = not notify_shown
        response = {"success": True, "notifications_displayed": notify_shown}
    except Exception as ex:
        log.exception("Error toggling notification display")
        response = {"success": False, "error": str(ex), "err_type": type(ex).__name__}
    finally:
        return jsonify(response)


@FLASK_APP.route("/get/notifications/status", methods=["GET"])
def get_notify_status():
    try:
        response = {"notifications_displayed": notify_shown}
    except Exception as ex:
        log.exception("Error fetching notification status")
        response = {"success": False, "error": str(ex), "err_type": type(ex).__name__}
    finally:
        return jsonify(response)


def log_console_output(min_timestamp: int = None):
    try:
        console_log = driver.get_log("browser")
        for entry in console_log:
            if entry["source"] == "console-api":
                level = logging.getLevelName(entry["level"])
                entry_timestamp = entry["timestamp"]
                if min_timestamp is None or entry_timestamp >= min_timestamp:
                    log.log(level, f"CONSOLE: {entry['message']}")
    except Exception as ex:
        log.exception("Console Log Error")
    finally:
        t = Timer(interval=30, function=log_console_output, args=(time.time(),))
        t.start()


def main():
    try:
        exit_code = 0
        subprocess.run("sudo systemctl restart hyperion", shell=True)
        global driver
        load_dotenv(dotenv_path=constants.env_dir / "datanode.env")
        options = Options()
        options.add_argument("--kiosk")
        options.add_argument("--noerrdialogs")
        options.add_argument("--disable-infobars")
        options.add_argument("--incognito")

        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        desired_capabilities = DesiredCapabilities.CHROME
        desired_capabilities["goog:loggingPrefs"] = {"browser": "ALL"}

        driver = webdriver.Chrome(options=options, desired_capabilities=desired_capabilities)
        global wait
        wait = WebDriverWait(driver, 20)
        loaded = False
        tries = 0
        while not loaded and tries < 10:
            try:
                log.info("Connecting to pihome webserver.")
                driver.get(constants.piframe_url)
                log_console_output()
                loaded = True
            except Exception as ex:
                if tries < 4:
                    log.error(
                        f"Could not connect to pihome webserver. Retrying ({tries+1} tries)..."
                    )
                    time.sleep(10)
                else:
                    log.exception(f"Site unreachable")
            finally:
                tries += 1
        global notify_shown
        notify_shown = False
        pyautogui.FAILSAFE = False
        ycord = pyautogui.size()[0]
        pyautogui.moveTo(0, ycord)
        FLASK_APP.run(host="0.0.0.0", port=8080, ssl_context="adhoc")
    except Exception:
        _, _, exc_tb = sys.exc_info()
        exit_code = exc_tb.tb_lineno
        log.exception("Fatal Error")
    finally:
        return exit_code


if __name__ == "__main__":
    log_filepath = constants.log_dir / "display_controller.log"
    log = get_logger(log_filepath)
    sys.exit(main())
