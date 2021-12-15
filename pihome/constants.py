#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Constants for use in pihome
File: constants
Project: PiHome
File Created: Tuesday, 26th October 2021 6:21:32 pm
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

from pathlib import Path

#: The root dir for pihome
root_dir = Path("/opt/pihome")
#: The log dir. Logs are kept here
log_dir = root_dir / "logs"
#: Script dir. Holds all executable scripts
script_dir = root_dir / "scripts"
#: Environment dir. Hold all env files.
env_dir = root_dir / ".env"
#: Data dir. Used for apps to store data.
data_dir = root_dir / "data"
#: Service dir. Holds all the systemd service files.
service_dir = root_dir / "services"
#: Lib dir. Holds all custom modules. This is symlinked on the Pi as pihome.
lib_dir = root_dir / "pihome"

font_dir = root_dir / "fonts"

#: The backup mount path. This is a mounted network drive.
mnt_dir = Path("/mnt/share")
#: Backup dir. Holds all backups.
backup_dir = mnt_dir / "pibackup"

#: Dir to hold any web server.
webserver_dir = root_dir / "webservers"
#: Dir pihome webserver.
pihome_webserver_dir = webserver_dir / "pihomeweb"
#: Dir to pihome webserver media.
pihome_webserver_media_dir = pihome_webserver_dir / "media"


#: The network drive path
mnt_location = "//GT-AC5300-F7A0/root/"

#: Tha database name
db_name = "pihome"

#: The dir for vault file storage
vault_dir = Path("~pi/hashicorp/vault-data").expanduser().resolve()

#: pihome url
pihome_base_url = "http://piframe.bw5808:8000/"
#:piframe url
piframe_url = pihome_base_url + "piframe/"
#:piinfo url
piinfo_url = pihome_base_url + "info/"

display_control_url = "https://piframe.bw5808:8080/"
display_slides_url = display_control_url + "show/slides"
display_info_url = display_control_url + "show/info"
display_system_url = display_control_url + "show/system"
display_toggle_notif_url = display_control_url + "toggle/notifications"
display_clear_notif_url = display_control_url + "clear/notifications"
display_notif_status_url = display_control_url + "get/notifications/status"


#: temp and humidity min max based on location
sensor_threshold = {
    "attic": {"temp": (30, 90), "humidity": (30, 70)},
    "upstairs": {"temp": (60, 80), "humidity": (35, 60)},
    "downstairs": {"temp": (60, 80), "humidity": (35, 60)},
}

nodes = [
    "pisensor1.bw5808",
    "pisensor2.bw5808",
    "pisensor3.bw5808",
    "piframe.bw5808",
    "pidisplay.bw5808",
]

ssh_key = Path("~pi/.ssh/id_rsa").expanduser()
