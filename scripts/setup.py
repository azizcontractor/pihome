#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Setup script for pihome
File: setup
Project: scripts
File Created: Tuesday, 26th October 2021 11:09:18 am
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

import argparse
import datetime as dt
import importlib
import os
import re
import shutil
import site
import socket
import subprocess
import sys
from pathlib import Path

try:
    import pihome.constants as constants
    from pihome.log import get_logger
except ImportError:
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from pihome import constants
    from pihome.log import get_logger

PY_PACKAGES = {
    "hvac": "hvac",
    "solaredge": "solaredge",
    "psycopg2": "psycopg2",
    "django": "django",
    "requests": "requests",
    "pytz": "pytz",
    "ipinfo": "ipinfo",
    "pyowm": "pyowm",
    "setuptools": "setuptools",
    "adafruit-circuitpython-dht": "adafruit_dht",
    "selenium": "selenium",
    "flask": "flask",
    "gpiozero": "gpiozero",
    "psutil": "psutil",
    "adafruit-circuitpython-neopixel": "neopixel",
}
APT_PACKAGES = [
    "git",
    "locate",
    "libpq-dev",
    "postgresql-client",
    "python3-pip",
    "libgpiod2",
]

DIRS = {constants.log_dir: 0o777, constants.mnt_dir: 0o777, constants.data_dir: 0o777}
FILES = {constants.script_dir: {"*": 0o775}}

FSTAB_LINE = (
    f"{constants.mnt_location} {constants.mnt_dir} cifs username=pi,password=aAc-5459,"
    "x-systemd.automount,_netdev,rw,vers=1.0,sec=ntlmssp 0 0"
)
FSTAB = "/etc/fstab"
SYSTEMD_PATH = Path("/etc/systemd/system")

SERVICES = {
    "common": ["healthcheck", "xdb"],
    "frame": [
        "vault",
        "unseal",
        "pihomebackup",
        "pihomeweb",
        "solarmonitor",
        "quotefetch",
        "hyperion",
    ],
    "sensor": ["envsense", "sensordisplay"],
    "display": ["picontrol"],
}

LOCATIONS = {"sensor1": "downstairs", "sensor2": "upstairs", "sensor3": "attic"}


def create_package_symlink():
    """
    Creates a symlink from pihome lib location '/opt/pihome/lib' to packages directory

    Raises:
        Exception: If lib dir does not exist
    """
    package_path = [Path(p) for p in site.getsitepackages() if "packages" in Path(p).name][0]
    log.info(f"Found package path at: {package_path}")
    lib_path = constants.lib_dir
    log.info(f"Looking for lib path: {lib_path}")
    sym_path = package_path / "pihome"
    if not (lib_path.exists() and lib_path.is_dir()):
        raise Exception("No lib directory found")
    if not (sym_path.exists() and sym_path.is_symlink() and Path.resolve(sym_path) == lib_path):
        log.info(f"Creating symlink {sym_path} -> {lib_path}")
        sym_path.symlink_to(lib_path, target_is_directory=True)
    else:
        log.info(f"Symlink already exists: {sym_path} -> {Path.resolve(sym_path)}")


def check_python_packages():
    """
    Checks if all the required packages are installed on the system.
    """
    log.info("Checking required Python packages are installed.")
    install_packages = []
    for package, import_name in PY_PACKAGES.items():
        try:
            importlib.import_module(import_name)
        except Exception as ex:
            log.error(f"{type(ex).__name__}: {str(ex)}")
            install_packages.append(package)
    if install_packages:
        log.info(f"Installing missing packages: {', '.join(install_packages)}")
        proc = subprocess.run(f"pip3 install {' '.join(install_packages)}", shell=True, check=True)
    else:
        log.info(f"All packages installed: {', '.join(PY_PACKAGES)}")


def check_apt_packages():
    """
    Install apt packages. Checks if packages are installed and installs them if needed. Uses APT
    CLI (unsafe)

    TODO: Use python-apt to install and check.
    """
    log.info("Checking required APT packages are installed.")
    install_packages = []
    for package in APT_PACKAGES:
        proc = subprocess.run(
            f"apt -qq list {package}", shell=True, check=True, capture_output=True, text=True
        )
        if "[installed]" not in proc.stdout:
            install_packages.append(package)
    if install_packages:
        subprocess.run("apt update", shell=True, check=True)
        log.info(f"Installing missing packages: {', '.join(install_packages)}")
        subprocess.run(f"apt install -y {' '.join(install_packages)}", shell=True, check=True)
    else:
        log.info(f"All packages installed: {', '.join(APT_PACKAGES)}")


def check_files_and_dirs():
    """
    Checks for existence of files and dirs and sets them to the correct mode
    """
    for dirpath, mode in DIRS.items():
        log.info(f"Checking {dirpath} exists and has the correct permissions")
        dirpath.mkdir(mode=mode, exist_ok=True)
        if not dirpath.is_mount():
            dirpath.chmod(mode)
    for dirpath in FILES:
        for glob, mode in FILES[dirpath].items():
            log.info(f"Updating files in dir {dirpath} that match glob {glob}")
            for fp in dirpath.glob(glob):
                fp.chmod(mode)


def mount_backup_drive():
    """
    Creates a mount point for the backup SMB disk.
    """
    with open(FSTAB, "r") as f:
        lines = [line.strip() for line in f]
    match = None
    changed = False
    for i, line in enumerate(lines):
        match = re.search(FSTAB_LINE, line)
        if match:
            log.info(f"FSTAB LINE: {line}")
            if line.startswith("#"):
                log.info(f"FSTAB line found at index {i+1} but commented. Uncommenting...")
                lines[i] = line.lstrip("#").lstrip()
                changed = True
            else:
                log.info(f"FSTAB line found at index {i+1} and is uncommented.")
    if not match:
        log.info("No FSTAB line found. Adding new line")
        lines.append(FSTAB_LINE)
        changed = True
    if changed:
        with open(FSTAB, "w") as f:
            f.write("\n".join(lines))
        log.info("Mounting drives.")
        subprocess.run("sudo mount -a", shell=True, check=True)
    constants.backup_dir.mkdir(exist_ok=True, mode=0o777)


def configure_services(node_type: str):
    service_types = ["common", node_type]
    for service_type in service_types:
        log.info(f"Configuring {service_type} services")
        for service in SERVICES.get(service_type, []):
            log.info(f"Configuring service {service}")
            service_path = constants.service_dir / f"{service}.service"
            sym_path = SYSTEMD_PATH / f"{service}.service"
            if not (
                sym_path.exists()
                and sym_path.is_symlink()
                and Path.resolve(sym_path) == service_path
            ):
                if sym_path.exists():
                    sym_path.unlink()
                log.info(f"Creating symlink {sym_path} -> {service_path}")
                sym_path.symlink_to(service_path)
            else:
                log.info(f"Symlink: {sym_path} -> {Path.resolve(sym_path)} already exists.")
    log.info("Reloading systemctl")
    subprocess.run("systemctl daemon-reload", shell=True, check=True)
    for service_type in service_types:
        log.info(f"Enabling and starting {service_type} services")
        for service in SERVICES.get(service_type, []):
            log.info(f"Enabling service {service}")
            subprocess.run(f"systemctl enable {service}", shell=True, check=True)
            log.info(f"Stopping service {service}")
            subprocess.run(f"systemctl stop {service}", shell=True, check=True)
            log.info(f"Starting service {service}")
            subprocess.run(f"systemctl start {service}", shell=True, check=True)
            log.info(f"Checking status of service {service}")
            subprocess.run(f"systemctl status {service}", shell=True)


def add_location_to_env():
    env_input_file = constants.env_dir / "sensornode_default.env"
    env_output_file = constants.env_dir / "sensornode.env"
    hostname = socket.gethostname()
    sensor_regex = r"pisensor(?P<num>\d+)"
    match = re.match(sensor_regex, hostname)
    if not match:
        raise ValueError(f"Invalid hostname {hostname}. Must match regex {sensor_regex}.")
    sensor_num = match.group("num")
    location = LOCATIONS[f"sensor{sensor_num}"]
    log.info(f"Location of sensor node determined: {location}")
    changed = False
    if env_output_file.exists():
        env_file = env_output_file
    else:
        env_file = env_input_file
    log.info(f"Loading env file: {env_file}")
    with open(env_file, "r") as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            key, value = re.split(r"\s*=\s*", line.strip(), maxsplit=1)
            if key == "LOCATION":
                if value != location:
                    log.info(f"Incorrect location found in env: {value}. Setting new loaction")
                    lines[i] = f"LOCATION={location}"
                    changed = True
                else:
                    log.info("No env file update required.")
                break
    if changed:
        log.info(f"Updating env file {env_output_file}")
        with open(env_output_file, "w") as f:
            f.write("".join(lines))


def add_display_control_autostart(desktop_file):
    log.info("Configuring display control autostart")
    autostart_dir = Path("/etc/xdg/autostart")
    sym_path = autostart_dir / desktop_file.name
    if not (sym_path.exists() and sym_path.is_symlink() and Path.resolve(sym_path) == desktop_file):
        if sym_path.exists():
            sym_path.unlink()
        log.info(f"Creating symlink {sym_path} -> {desktop_file}")
        sym_path.symlink_to(desktop_file)
    else:
        log.info(f"Symlink: {sym_path} -> {Path.resolve(sym_path)} already exists.")
    subprocess.run(f"systemctl restart display-manager", shell=True, check=True)


def add_pixel_font():
    font_file = constants.font_dir / "PixelOperator.ttf"
    base_font_dir = Path("/usr/share/fonts")
    pixel_font_dir = base_font_dir / "PixelOperator"
    pixel_font_dir.mkdir(exist_ok=True)
    log.info(f"Copying {font_file} to {pixel_font_dir}")
    shutil.copy2(font_file, pixel_font_dir)


def main(node_type: str) -> int:
    """
    The main function that controls logic flow

    Args:
        node_type (str): The node type to run setup for. THis dictates node specific operations.

    Returns:
        int: The exit code: 0 for success 1 for failure.
    """
    try:
        exit_code = 0
        if node_type not in ["frame", "sensor", "display"]:
            raise Exception(f"Invalid Node type: {node_type}")
        else:
            log.info(f"Starting script for {node_type} node.")
        check_files_and_dirs()
        mount_backup_drive()
        create_package_symlink()
        check_apt_packages()
        check_python_packages()
        if node_type == "sensor":
            add_location_to_env()
            add_pixel_font()
        if node_type == "frame":
            desktop_file = constants.service_dir / "pihome-browser.desktop"
            add_display_control_autostart(desktop_file)
        if node_type == "display":
            desktop_file = constants.service_dir / "picontrol-browser.desktop"
            add_display_control_autostart(desktop_file)
        configure_services(node_type)
    except Exception:
        log.exception("Fatal Error")
        exit_code = 1
    finally:
        return exit_code


def get_node_type():
    hostname = socket.gethostname()
    node_type_regex = r"^pi(?P<nodetype>[a-zA-Z]+)\d*$"
    m = re.search(node_type_regex, hostname)
    if m:
        return m.group("nodetype")
    else:
        return None


if __name__ == "__main__":
    if not os.geteuid() == 0:
        print("This script must be run as root")
        sys.exit(1)
    constants.log_dir.mkdir(mode=0o777, exist_ok=True)
    log_filepath = (
        constants.log_dir / f"pihome_setup_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    log = get_logger(log_filepath, backup_count=0)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--node_type",
        type=str,
        help="The type of node setup to run.",
        choices=["frame", "sensor", "display"],
        default=get_node_type(),
    )
    args = parser.parse_args()
    sys.exit(main(args.node_type))
