#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Views for home information
File: views
Project: PiHome
File Created: Friday, 5th November 2021 9:25:40 am
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

import pihole as ph
from django.db import connections
from django.http import Http404, HttpRequest, JsonResponse
from django.shortcuts import render
from pihome.router import RouterMgr
from pihome.vault import VaultMgr

_LOG = logging.getLogger(__name__)


# Create your views here.
def index(request: HttpRequest):
    return render(request, "data_index.html", {})


def load_solar_data(request: HttpRequest):
    if not request.is_ajax():
        raise Http404("Page not found")
    with connections["solar"].cursor() as c:
        c.execute("SELECT * FROM energy WHERE date = %s", (dt.date.today(),))
        row = c.fetchone()
        cols = [col.name for col in c.description]
        energy_data = {col: item for col, item in zip(cols, row)}
        c.execute(
            "SELECT * FROM power WHERE DATE(datetime) = %s AND datetime = "
            "(SELECT MAX(datetime) FROM power)",
            (dt.date.today(),),
        )
        row = c.fetchone()
        cols = [col.name for col in c.description]
        power_data = {col: item for col, item in zip(cols, row)}
    resp = {"power": power_data, "energy": energy_data}
    if power_data["datetime"] < dt.datetime.now() - dt.timedelta(minutes=15):
        resp["update_late"] = True
    else:
        resp["update_late"] = False
    _LOG.info(resp)
    return JsonResponse(resp)


def load_sensor_data(request: HttpRequest):
    if not request.is_ajax():
        raise Http404("Page not found")
    icon_classes = {
        "upstairs": "fas fa-sort-amount-up-alt fa-7x",
        "downstairs": "fas fa-sort-amount-down-alt fa-7x",
        "attic": "fas fa-igloo fa-7x",
    }
    with connections["sensor"].cursor() as c:
        c.execute(
            "SELECT location, MAX(datetime) FROM environment WHERE DATE(datetime) = %s "
            "GROUP BY location",
            (dt.date.today(),),
        )
        rows = c.fetchall()
        sensor_data = {
            loc.title(): {"updated": timestamp, "icon-class": icon_classes[loc]}
            for loc, timestamp in rows
        }
        for loc, timestamp in rows:
            c.execute(
                "SELECT temperature,humidity FROM environment "
                "WHERE location = %s AND datetime = %s",
                (loc, timestamp),
            )
            row = c.fetchone()
            sensor_data[loc.title()]["temperature"] = row[0]
            sensor_data[loc.title()]["humidity"] = row[1]
            if sensor_data[loc.title()]["updated"] <= dt.datetime.now() - dt.timedelta(minutes=5):
                sensor_data[loc.title()]["update_late"] = True
            else:
                sensor_data[loc.title()]["update_late"] = False
    _LOG.info(sensor_data)
    return JsonResponse(sensor_data)


def load_network_data(request: HttpRequest):
    if not request.is_ajax():
        raise Http404("Page not found")
    vault = VaultMgr(os.getenv("VAULT_URL"), os.getenv("ROLE_ID"), os.getenv("SECRET_ID"))
    router_data = vault.get_secret("network/router")
    router = RouterMgr(**router_data)
    wan_data = router.get_status_wan()
    resp = {
        "wan_status": wan_data["statusstr"].strip("'"),
        "ip": wan_data["ipaddr"].strip("'"),
        "piholes": {},
    }
    if wan_data["statusstr"].strip("'").lower() == "connected":
        resp["wan_icon"] = "fas fa-wifi fa-7x w3-text-green"
    else:
        resp["wan_icon"] = "fas fa-exclamation-triangle fa-7x w3-text-red"
    pihole_data = vault.get_secret("network/pihole")
    for ph_host, ph_info in pihole_data.items():
        pihole = ph.PiHole(ph_info["ip"])
        pihole.authenticate(ph_info["password"])
        pihole.refresh()
        ph_dict = {
            "status": pihole.status.title(),
            "queries": pihole.queries,
            "blocked": pihole.blocked,
            "ads": pihole.ads_percentage,
            "clients": pihole.total_clients,
        }
        version_info = pihole.getVersion()
        _LOG.info(version_info)
        if pihole.status == "enabled":
            ph_dict["icon"] = "fas fa-shield-alt fa-7x w3-text-green"
        else:
            ph_dict["icon"] = "fas fa-shield-virus fa-7x w3-text-red"
        if any(
            [
                version_info["core_update"],
                version_info["web_update"],
                version_info["FTL_update"],
            ]
        ):
            ph_dict["icon"].replace("w3-text-green", "w3-text-yellow")
        resp["piholes"][ph_host] = ph_dict
    _LOG.info(resp)
    return JsonResponse(resp)
