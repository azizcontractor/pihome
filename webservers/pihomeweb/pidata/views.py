#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Weather and location data display for PiHome
File: views
Project: PiHome
File Created: Thursday, 4th November 2021 12:15:50 pm
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
import time

import ipinfo
import pyowm
from django.http import Http404, HttpRequest, JsonResponse
from pihome.vault import VaultMgr
from django.db import connections
from dateutil import tz

# Create your views here.
ipinfo_token_path = "sensor/ipinfo"
owm_token_path = "sensor/openweathermap"
update_interval_mins = 30

_LOG = logging.getLogger(__name__)


def load_time(request: HttpRequest):
    if not request.is_ajax():
        raise Http404("Page not found")
    resp = {"time": dt.datetime.now().strftime("%-I:%M %p")}
    return JsonResponse(resp)


def load_location(request: HttpRequest):
    if not request.is_ajax():
        raise Http404("Page not found")
    now = dt.datetime.now()
    vault = VaultMgr(os.getenv("VAULT_URL"), os.getenv("ROLE_ID"), os.getenv("SECRET_ID"))
    last_update = dt.datetime.strptime(
        request.session.get("location_last_update", "20200101_010101"), "%Y%m%d_%H%M%S"
    )
    _LOG.info(f"Location Last updated: {last_update}")
    if last_update is None or last_update + dt.timedelta(minutes=update_interval_mins) <= now:
        _LOG.info("Fetching new location.")
        token = vault.get_secret(ipinfo_token_path)["token"]
        handler = ipinfo.getHandler(token)
        details = handler.getDetails()
        location_data = details.all
        request.session["location_last_update"] = now.strftime("%Y%m%d_%H%M%S")
        request.session["location_data"] = location_data
        _LOG.info(f"Location detials: {location_data}")
    else:
        _LOG.info("Using cached location data")
        location_data = request.session["location_data"]
    return JsonResponse(location_data)


def load_weather(request: HttpRequest):
    if not request.is_ajax():
        raise Http404("Page not found")
    local_tz = tz.tzlocal()
    lat = float(request.GET["lat"])
    lon = float(request.GET["lon"])
    now = dt.datetime.now()
    last_update = dt.datetime.strptime(
        request.session.get("weather_last_update", "20200101_010101"), "%Y%m%d_%H%M%S"
    )
    _LOG.info(f"Weather Last updated: {last_update}")
    if last_update is None or last_update + dt.timedelta(minutes=update_interval_mins) <= now:
        _LOG.info("Fetching new weather data.")
        vault = VaultMgr(os.getenv("VAULT_URL"), os.getenv("ROLE_ID"), os.getenv("SECRET_ID"))
        api_key = vault.get_secret(owm_token_path)["api_key"]
        owm = pyowm.OWM(api_key)
        mgr = owm.weather_manager()
        one_call = mgr.one_call(lat=lat, lon=lon, unites="imperial")
        forecast_data = []
        weather_data = {
            "temp": one_call.current.temperature("fahrenheit"),
            "icon": one_call.current.weather_icon_url(size="2x"),
            "detailed_status": one_call.current.detailed_status.title(),
            "status": one_call.current.status.title(),
        }
        forecast = one_call.forecast_daily
        for weather in forecast[:5]:
            forecast_data.append(
                {
                    "day": weather.reference_time("date")
                    .astimezone(local_tz)
                    .strftime("%a\n%m/%d"),
                    "temp_min": int(round(weather.temperature("fahrenheit")["min"], 0)),
                    "temp_max": int(round(weather.temperature("fahrenheit")["max"], 0)),
                    "status": weather.status.title(),
                    "icon": weather.weather_icon_url(),
                }
            )
        weather_data["forecast"] = forecast_data
        sunset = one_call.current.sunset_time()
        sunrise = one_call.current.sunrise_time()
        _LOG.info(weather_data)
        if sunrise <= time.time() <= sunset:
            weather_data["bg_color"] = "w3-blue"
        else:
            weather_data["bg_color"] = "w3-gray"
        request.session["weather_last_update"] = now.strftime("%Y%m%d_%H%M%S")
        request.session["weather_data"] = weather_data
    else:
        _LOG.info("Using cached weather data.")
        weather_data = request.session["weather_data"]
    return JsonResponse(weather_data)


def load_quote(request: HttpRequest):
    with connections["quote"].cursor() as c:
        c.execute(
            "SELECT * FROM qotd WHERE DATE(datetime) = %s ORDER BY datetime DESC LIMIT 1",
            (dt.date.today(),),
        )
        row = c.fetchone()
        cols = [col.name for col in c.description]
        quote_data = {col: item for col, item in zip(cols, row)}
    if quote_data["datetime"].date() != dt.date.today():
        quote_data["update_late"] = True
    else:
        quote_data["update_late"] = False
    return JsonResponse(quote_data)


def load_notifications(request: HttpRequest):
    with connections["report"].cursor() as c:
        c.execute(
            "SELECT datetime,node,app,type,msg FROM notifications WHERE status=%s "
            "ORDER BY datetime ASC LIMIT 10",
            ("unread",),
        )
        rows = c.fetchall()
        cols = [col.name for col in c.description]
        notifications = []
        for row in rows:
            data = {col: item for item, col in zip(row, cols)}
            data["display_datetime"] = data["datetime"].strftime("%m/%d/%Y %-I:%M %p")
            data["real_datetime"] = data["datetime"].strftime("%Y%m%d_%H%M%S%f")
            notifications.append(data)
        c.execute("SELECT COUNT(*) FROM notifications WHERE status=%s", ("unread",))
        count = c.fetchone()[0]
    resp = {"notifications": notifications, "displayed": len(rows), "total": count}
    return JsonResponse(resp)


def clear_notification(request: HttpRequest):
    datetime = dt.datetime.strptime(request.GET["datetime"], "%Y%m%d_%H%M%S%f")
    app = request.GET["app"]
    node = request.GET["node"]
    _LOG.info(f"Marking notification as read: datetime>{datetime}, app>{app}, node>{node}")
    with connections["report"].cursor() as c:
        c.execute(
            "UPDATE notifications SET status=%s WHERE datetime=%s AND app=%s and node=%s",
            ("read", datetime, app, node),
        )
    return JsonResponse({"success": True})


def clear_all_notifications(request: HttpRequest):
    _LOG.info("Marking first 10 notifications as read.")
    with connections["report"].cursor() as c:
        c.execute(
            "UPDATE notifications SET status=%s WHERE (datetime,app,node) IN "
            "(SELECT datetime,app,node FROM notifications WHERE status=%s "
            "ORDER BY datetime ASC LIMIT 10)",
            ("read", "unread"),
        )
    return JsonResponse({"success": True})
