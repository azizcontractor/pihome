import datetime as dt
import logging
import socket
import subprocess
import time

import paramiko
import pihome.constants as constants
import requests
from django.http import Http404, HttpRequest, JsonResponse
from django.shortcuts import redirect, render

_LOG = logging.getLogger(__name__)

# Create your views here.
def index(request: HttpRequest):
    resp = requests.get(constants.display_notif_status_url, verify=False)
    resp.raise_for_status()
    notif_status = resp.json()["notifications_displayed"]
    return render(request, "home_index.html", {"notify_shown": notif_status})


def show_info(request: HttpRequest):
    resp = requests.get(constants.display_info_url, verify=False)
    resp.raise_for_status()
    if not resp.json().get("success", False):
        _LOG.info(f"Could not show home info.{resp}")
    return redirect("home:index")


def show_slides(request: HttpRequest):
    resp = requests.get(constants.display_slides_url, verify=False)
    resp.raise_for_status()
    if not resp.json().get("success", False):
        _LOG.info(f"Could not show slideshow.{resp}")
    return redirect("home:index")


def show_system(request: HttpRequest):
    resp = requests.get(constants.display_system_url, verify=False)
    resp.raise_for_status()
    if not resp.json().get("success", False):
        _LOG.info(f"Could not show system info.{resp}")
    return redirect("home:index")


def toggle_notifications(request: HttpRequest):
    resp = requests.get(constants.display_toggle_notif_url, verify=False)
    resp.raise_for_status()
    if not resp.json().get("success", False):
        _LOG.info(f"Could not toggle notifications.{resp}")
    return redirect("home:index")


def clear_notifications(request: HttpRequest):
    resp = requests.get(constants.display_clear_notif_url, verify=False)
    resp.raise_for_status()
    if not resp.json().get("success", False):
        _LOG.info(f"Could not clear notifications.{resp}")
    return redirect("home:index")


def system_reboot(request: HttpRequest):
    if not request.is_ajax():
        raise Http404("Page not found")
    resp = {}
    hostname = socket.gethostname()
    nodes = [node for node in constants.nodes if node.split(".")[0] != hostname]
    for node in nodes:
        _LOG.info(f"Rebooting Node {node}.")
        try:
            reboot(node)
            resp[node] = True
        except Exception:
            _LOG.exception("Connect and Reboot Error")
            resp[node] = False
    subprocess.run("sudo reboot", shell=True)
    return JsonResponse(resp)


def reboot(hostname: str):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    _LOG.info(f"Connecting to {hostname}")
    ssh.connect(hostname, key_filename=str(constants.ssh_key), username="pi")
    try:
        ssh.exec_command("sudo /sbin/reboot  > /dev/null 2>&1 &")
    except Exception:
        _LOG.exception("REBOOT ERROR")

    reboot_start = False
    start = dt.datetime.now()
    while not reboot_start and start + dt.timedelta(seconds=15) >= dt.datetime.now():
        proc = subprocess.run(f"ping -c 1 {hostname}", shell=True)
        reboot_start = proc.returncode != 0
        time.sleep(1)
    _LOG.info(f"Waiting for {hostname} to finish rebooting.")
    rebooted = False
    start = dt.datetime.now()
    _LOG.info(f"Pinging {hostname}")
    while not rebooted and start + dt.timedelta(seconds=55) >= dt.datetime.now():
        proc = subprocess.run(f"ping -c 1 {hostname}", shell=True)
        rebooted = proc.returncode == 0
        time.sleep(1)
    if not rebooted:
        _LOG.warning(f"{hostname} did not come back up in 30 seconds. Something may be wrong.")
    else:
        _LOG.info(f"{hostname} replied to ping. Status is up.")
