#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Manages the database for pihome
File: db_mgr
Project: lib
File Created: Monday, 25th October 2021 9:46:05 pm
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
import psycopg2


class DBMgr:
    def __init__(self, host: str, user: str, password: str, database: str, schema: str) -> None:
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.schema = schema
        self.conn = psycopg2.connect(host=host, user=user, password=password, dbname=database)
