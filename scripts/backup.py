#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Manages system backups daily
File: backup
Project: PiHome
File Created: Thursday, 28th October 2021 6:24:31 pm
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
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

import pihome.constants as constants
from pihome.log import get_logger
from pihome.shared import GracefulExit

PG_DUMP = "/usr/bin/pg_dump"


def cleanup_old_backups(dirpath: Path, keep_days: int = 3):
    """
    Deletes files older than keep_days parameter on the given dirpath. This ensures that diskspace
    does not get full. Deletes both files and dirs that match the criteria. Uses shutil rmtree
    to delete dirs in case they are nonempty.

    Args:
        dirpath (Path): The dir to delete files and dirs from.
        keep_days (int, optional): Number of days to keep. The file mtime delta is compared to this
        value. Defaults to 3.
    """
    log.info(f"Cleaning up old backups in {dirpath}")
    for fp in dirpath.glob("*"):
        mtime = dt.datetime.fromtimestamp(fp.stat().st_mtime)
        if (dt.datetime.now() - mtime).days > keep_days:
            log.debug(f"Deleting file {fp} since it has mtime {mtime}.")
            if fp.is_file():
                fp.unlink()
            else:
                shutil.rmtree(fp)


def backup_db():
    """
    Backs up the database as a dir. Uses pg_dump to backup the DB. The flags supplied to pg_dump
    control the backup type. The backup is stored on the network shared drive. Current flags
    provided to the pg_dump command are described in the note below.

    Note:
        -Fd -> Backup database as a directory. Each table is a separate file.
        -j 5 -> Run 5 jobs in parallel to backup the DB. Makes the backup quicker but puts a load on
            the database.
        -v -> Verbose backup so that data can be written to log file.
    """
    log.info("Backing up database.")
    root_backup_dir = constants.backup_dir / "db"
    root_backup_dir.mkdir(mode=0o775, exist_ok=True)
    backup_dir = root_backup_dir / f"dump_{dt.date.today().strftime('%Y%m%d')}"
    cleanup_old_backups(root_backup_dir)
    cmd = f"{PG_DUMP} {constants.db_name} -Fd -f {backup_dir} -j 5 -v"
    log.info(f"Running backup command: {cmd}")
    try:
        proc = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.CalledProcessError as ex:
        log.exception("DB Backup Error.")
        stdout = ex.stdout
        stderr = ex.stderr
    finally:
        log.info("STDOUT LINES:")
        log.info("=" * 80)
        for line in stdout.splitlines():
            log.info(line)
        log.info("=" * 80)
        log.info("STDERR LINES:")
        log.info("=" * 80)
        for line in stderr.splitlines():
            log.info(line)
        log.info("=" * 80)


def backup_vault():
    """
    Backs up the vault data to the network share. Vault does not recommend this type of backup
    without shutting down the vault server. The assumption made here is that vault data will rarely
    be written to and only mostly read from. This is why this type of backup may actually work.

    TODO: Research more backup types where online backups can be made. Maybe set vault backend to
        the database so that DB backups can cover vault backups as well.
    """
    log.info("Backing up vault data.")
    vault_dir = constants.vault_dir
    backup_dir = constants.backup_dir / "vault"
    backup_dir.mkdir(mode=0o775, exist_ok=True)
    backup_file = backup_dir / f"vault_{dt.date.today().strftime('%Y%m%d')}.tar.gz"
    cleanup_old_backups(backup_dir)
    try:
        with tarfile.open(backup_file, "w:gz") as tar:
            tar.add(vault_dir, vault_dir.name)
        log.info(f"TAR file created at {backup_file}")
    except Exception as ex:
        log.exception("Could not create tarfile.")


def backup_pihome_media():
    """
    Backs up the pihome media directory since it has user uploaded images. Stores these images
    in backup so that they can be retrieved.
    """
    log.info("Backing up pihome media data.")
    vault_dir = constants.pihome_webserver_media_dir
    backup_dir = constants.backup_dir / "pihome_media"
    backup_dir.mkdir(mode=0o775, exist_ok=True)
    backup_file = backup_dir / f"pihome_media_{dt.date.today().strftime('%Y%m%d')}.tar.gz"
    cleanup_old_backups(backup_dir)
    try:
        with tarfile.open(backup_file, "w:gz") as tar:
            tar.add(vault_dir, vault_dir.name)
        log.info(f"TAR file created at {backup_file}")
    except Exception as ex:
        log.exception("Could not create tarfile.")


def main() -> int:
    """
    Main function to control logic flow. IF there is a fatal error this function will exit with the
    line number of the error otherwise the exit code will be 0.

    Returns:
        int: The exit code to exit with.
    """
    try:
        exit_code = 0
        exit_control = GracefulExit()
        timeout = 0.5
        log.info("Starting backup service.")
        while not exit_control.exit_now.wait(timeout=timeout):
            if dt.datetime.now().hour == 13:
                backup_db()
                backup_vault()
                backup_pihome_media()
            next_hour = (dt.datetime.now() + dt.timedelta(hours=1)).replace(
                second=10, minute=0, microsecond=0
            )
            timeout = (next_hour - dt.datetime.now()).total_seconds()
            log.info(f"Waiting for next hour: {next_hour}")
    except Exception:
        _, _, exc_tb = sys.exc_info()
        exit_code = exc_tb.tb_lineno
        log.exception("FATAL ERROR")
    finally:
        log.info("Exiting backup service.")
        return exit_code


if __name__ == "__main__":
    log_filepath = constants.log_dir / f"backup_mgr.log"
    log = get_logger(log_filepath, backup_count=0)
    sys.exit(main())
