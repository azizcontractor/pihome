#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Show stats on I2C screen
File: i2c_stats
Project: PiHome
File Created: Saturday, 27th November 2021 9:53:13 am
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

import math
import shutil
import socket
import time

import adafruit_ssd1306
import board
import digitalio
import gpiozero
import psutil
from PIL import Image, ImageDraw, ImageFont


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(("192.168.50.1", 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = int(round(size_bytes / p, 0))
    return f"{s} {size_name[i]}"


if __name__ == "__main__":
    # Define the Reset Pin
    oled_reset = digitalio.DigitalInOut(board.D4)

    # Display Parameters
    WIDTH = 128
    HEIGHT = 32

    # Use for I2C.
    i2c = board.I2C()
    oled = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=0x3C, reset=oled_reset)

    # Clear display.
    oled.fill(0)
    oled.show()

    # Create blank image for drawing.
    # Make sure to create image with mode '1' for 1-bit color.
    image = Image.new("1", (oled.width, oled.height))

    # Get drawing object to draw on image.
    draw = ImageDraw.Draw(image)

    # Draw a white background
    draw.rectangle((0, 0, oled.width, oled.height), outline=255, fill=255)

    font = ImageFont.truetype("PixelOperator.ttf", 16)
    cpu = gpiozero.CPUTemperature()
    while True:
        # Draw a black filled box to clear the image.
        draw.rectangle((0, 0, oled.width, oled.height), outline=0, fill=0)

        IP = f"IP: {get_ip()}"
        CPU = f"CPU: {round(psutil.cpu_percent(),1)}%"
        mem_tuple = psutil.virtual_memory()
        used_mem = convert_size(mem_tuple.used)
        total_mem = convert_size(mem_tuple.total)
        MemUsage = f"Mem: {used_mem} / {total_mem}"
        disk_tuple = shutil.disk_usage("/")
        used_disk = convert_size(disk_tuple.used)
        total_disk = convert_size(disk_tuple.total)
        Disk = f"Disk: {used_disk} / {total_disk}"
        temp = f"{round(cpu.temperature,0)} \u00b0C"

        # Pi Stats Display
        draw.text((0, 0), IP, font=font, fill=255)
        draw.text((0, 16), CPU, font=font, fill=255)
        draw.text((80, 16), temp, font=font, fill=255)
        draw.text((0, 32), MemUsage, font=font, fill=255)
        draw.text((0, 48), Disk, font=font, fill=255)

        # Display image
        oled.image(image)
        oled.show()
        time.sleep(0.1)
