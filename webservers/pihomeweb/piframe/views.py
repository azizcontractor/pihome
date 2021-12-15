#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Views for piframe app
File: views
Project: PiHome
File Created: Tuesday, 2nd November 2021 7:08:26 pm
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
import random
import threading
import time

import board
import neopixel
from django.conf.global_settings import MEDIA_ROOT
from django.http import Http404, HttpRequest, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from PIL import Image

from .forms import UploadForm
from .models import Slide
from typing import Tuple

IMAGE_EXT = {".jpg": "JPEG", ".png": "PNG"}

PIFRAME_IP = "192.168.50.77"

_LOG = logging.getLogger(__name__)

# LED_COUNT = 60  # Number of LED pixels.
# LED_PIN = 18  # GPIO pin connected to the pixels (18 uses PWM!).
# LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
# LED_DMA = 10  # DMA channel to use for generating signal (try 10)
# LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
# LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
# LED_CHANNEL = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53

# strip = Adafruit_NeoPixel(
#     LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL
# )
# # Intialize the library (must be called once before other functions).
# strip.begin()

# Create your views here.
def index(request: HttpRequest):
    return render(request, "pic_index.html", {})


def manage_images(request: HttpRequest):
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("piframe:manage")
    else:
        form = UploadForm()
        images = Slide.objects.all()
        img_dict = {img.id: img.image.url for img in images}

    return render(request, "manage_piframe.html", {"form": form, "images": img_dict})


@require_POST
def delete_image(request: HttpRequest):
    img_id = request.POST["img_id"]
    img = Slide.objects.get(id=img_id)
    img.delete()
    return redirect("piframe:manage")


def load_image(request: HttpRequest):
    if not request.is_ajax():
        raise Http404("Page does not exist")
    max_width = float(request.GET["width"])
    max_height = float(request.GET["height"])
    images = Slide.objects.all()
    resp = {}
    if images:
        img = random.choice(images)
        _LOG.info(f"Opening: {img.image.path}")
        resp["image"] = img.image.url
    else:
        resp["image"] = None
    return JsonResponse(resp)


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms / 1000.0)
