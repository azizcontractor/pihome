#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Homepage for PiHome
File: views
Project: PiHome
File Created: Monday, 8th November 2021 12:06:42 pm
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

from django.db import connections
from django.http import Http404, HttpRequest, JsonResponse
from django.shortcuts import render

# Create your views here.
def index(request: HttpRequest):
    return render(request, "home_index.html", {})


def get_stats(request: HttpRequest):
    if not request.is_ajax():
        raise Http404("Page not found")
    with connections["report"].cursor() as c:
        c.execute(
            "SELECT nodename, MAX(datetime) FROM system_stats WHERE DATE(datetime) = %s "
            "GROUP BY nodename",
            (dt.date.today(),),
        )
        rows = c.fetchall()
        node_data = {node: {"updated": timestamp} for node, timestamp in rows}
        for node, timestamp in rows:
            node_data[node]["update_late"] = dt.datetime.now() > timestamp + dt.timedelta(
                minutes=15
            )
            c.execute(
                "SELECT cpu_temp,cpu_usage,mem_usage,disk_usage,disk_total,location,uptime FROM "
                "system_stats WHERE nodename = %s AND datetime = %s",
                (node, timestamp),
            )
            row = c.fetchone()
            node_data[node]["CPU Temperature"] = f"{round(row[0],2)}\u00b0 C"
            node_data[node]["CPU Usage"] = f"{round(row[1],2)}%"
            node_data[node]["Memory Usage"] = f"{round(row[2],2)}%"
            node_data[node]["Disk"] = (
                f"{int(round(row[3]/1024**3))} GB / {int(round(row[4]/1024**3))} GB "
                f"({round((row[3]/row[4])*100,2)}%)"
            )
            node_data[node]["Uptime"] = row[6].title()
            if "sensor" in node:
                node_data[node]["Location"] = row[5].title()

    return JsonResponse(node_data)
