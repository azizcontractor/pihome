#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Description of script
File: db
Project: PiHome
File Created: Wednesday, 27th October 2021 11:05:38 pm
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
import threading
from typing import Any, Dict, List, Tuple, Union

import psycopg2

import pihome.constants as constants
from pihome.exceptions import DBConnectionError
from pihome.shared import load_json_data, write_json_data

_LOG = logging.getLogger(__name__)


class DBMgr:
    """
    This class is responsible for managing the database. Allows the user to insert, update, fetch,
    and delete data from the db without writing any sql queries. If a DB connection is not available
    then data is written to a file. The system should have a separate xdb process that can update
    the databse from the file.

    Attributes:
        xdb_file (Path): The path to the XDB file.
        retry_interval (int): The number of seconds to wait before retrying a failed DB update.
        db_params (Dict[str,str]): Containing all the necessary information to connect to the
            DB.
        host (str): The database host.
        user (str): The user to connect to the DB as.
        conn (psycopg2.connection): The connection to the DB.
    """

    xdb_dir = constants.data_dir
    retry_interval = 300

    def __init__(
        self,
        host: str,
        port: int,
        dbname: str,
        user: str,
        password: str,
        options: str = None,
        **kwargs,
    ) -> None:
        """
        Initializes the DB manager.

        Args:
            host (str): The hostname to connect to.
            port (int): The port used for the connection.
            dbname (str): The database name.
            user (str): The user to connect as
            password (str): The password for the connection.
            options (str, optional): Extra options to passed on to psycopg2. Defaults to None.

        Keyword Args:
            All kwargs are passed on to the psycopg2 connection attribute.
        """
        self.db_params = {
            "host": host,
            "port": port,
            "dbname": dbname,
            "user": user,
            "password": password,
        }
        if options is not None:
            self.db_params["options"] = options
        if kwargs:
            self.db_params.update(kwargs)
        self.host = host
        self.dbname = dbname
        self.user = user
        self.db_options = options
        self.db_kwargs = kwargs
        self.conn = None
        self.connect()

    def exit(self):
        """
        Closes the DB manager. Closes the connection and stops the xdb thread.
        """
        if self.is_connected():
            _LOG.info("Closing DB connection.")
            self.conn.close()

    def connect(self):
        """
        Connect to the DB server. Only connects if a previous connection is not present.
        """
        try:
            if not self.is_connected():
                self.conn = psycopg2.connect(**self.db_params)
            _LOG.info(f"Connected to DB {self.dbname} on {self.host} as {self.user}")
        except Exception as ex:
            _LOG.error(f"{type(ex).__name__}: {str(ex)}")
            _LOG.warning(
                "Failed to connect to DB. Queries will be written to a file until DB connection "
                "can be re-established."
            )
            self.conn = None

    def is_connected(self) -> bool:
        """
        Checks if the DB server is connected. Runs a simple query as a test.

        Returns:
            bool: True if connected. False otherwise.
        """
        if self.conn is None or self.conn.closed:
            return False
        try:
            with self.conn:
                with self.conn.cursor() as c:
                    c.execute("SELECT NOW()")
                    row = c.fetchone()
                    if row:
                        connected = True
        except Exception as ex:
            connected = False
        finally:
            return connected

    def insert_data(
        self, table: str, data: Union[Dict[str, Any], List[Dict[str, Any]]], update_xdb: bool = True
    ):
        """
        Insert data into a table. This function automatically generates the sql required for the
        insert. If data param is a list, then it assumes that many rows need to be inserted;
        otherwise a single row insert is performed when data is a dict. The data dictionary keys
        are the column names as they appear in the table and the values are the values that need
        to be inserted.

        Args:
            table (str): The table name to insert data into.
            data (Union[Dict[str, Any], List[Dict[str, Any]]]): The data to insert. List of dicts
                inserts multiple rows and a dict inserts a single row.
            update_xdb (bool, optional): Indicates whether to write data to xdb file if insert
                fails. Defaults to True.

        Raises:
            NoConnection: If connection to the DB could not be established.
        """
        if isinstance(data, list):
            cols = data[0].keys()
        else:
            cols = data.keys()
        col_str = ", ".join(f"%({col})s" for col in cols)
        sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({col_str})"
        try:
            if not self.is_connected():
                self.connect()
            if self.conn is None:
                raise DBConnectionError("No connection to database.")
            with self.conn:
                with self.conn.cursor() as c:
                    _LOG.info(f"Executing query: {sql}")
                    if isinstance(data, list):
                        c.executemany(sql, data)
                    else:
                        c.execute(sql, data)
            _LOG.info("Data inserted successfully")
        except (psycopg2.OperationalError, DBConnectionError) as ex:
            _LOG.error(f"{type(ex).__name__}: {str(ex)}")
            if update_xdb:
                _LOG.warning(f"Connection error. Data Will be written to file to be updated later.")
                self.write_xdb("insert", {"table": table, "data": data})
            else:
                raise

    def update_data(
        self,
        table: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        key_cols: List[str],
        update_xdb: bool = True,
    ):
        """
        Updates a row in the table if it exists. This function automatically generates the sql
        required for the update. If data param is a list, then it assumes that many rows need to be
        updated; otherwise a single row update is performed when data is a dict. The data dictionary
        keys are the column names as they appear in the table and the values are the values that
        need to be updated. The key_cols parameter is a list of column names that form the WHERE
        clause. In addition to being in the key_cols list, constraint parameters must also be in the
        data dict as key/value pairs.

        Args:
            table (str): The table name to update the data for.
            data (Union[Dict[str, Any], List[Dict[str, Any]]]): The data to update. List of dicts
                updates multiple rows and a dict updates a single row.
            key_cols (List[str]): The columns part of the where clause. These must also be present
                in the data dict.
            update_xdb (bool, optional): Indicates whether to write data to xdb file if insert
                fails. Defaults to True.

        Raises:
            NoConnection: If connection to the DB could not be established.
        """
        if isinstance(data, list):
            cols = data[0].keys()
        else:
            cols = data.keys()
        col_str = ", ".join(f"{col} = %({col})s" for col in cols if col not in key_cols)
        key_col_str = " AND ".join(f"{col} = %({col})s" for col in key_cols)
        sql = f"UPDATE {table} SET {col_str} WHERE {key_col_str}"
        try:
            if not self.is_connected():
                self.connect()
            if self.conn is None:
                raise DBConnectionError("No connection to database.")
            with self.conn:
                with self.conn.cursor() as c:
                    _LOG.info(f"Executing query: {sql}")
                    if isinstance(data, list):
                        c.executemany(sql, data)
                    else:
                        c.execute(sql, data)
        except (psycopg2.OperationalError, DBConnectionError) as ex:
            _LOG.error(f"{type(ex).__name__}: {str(ex)}")
            if update_xdb:
                _LOG.warning(f"Connection error. Data Will be written to file to updated later.")
                self.write_xdb("update", {"table": table, "data": data, "key_cols": key_cols})
            else:
                raise
        _LOG.info("Data updated successfully")

    def fetch_data(
        self,
        table: str,
        cols: List[str] = None,
        condition: Dict[str, Any] = {},
        single_row: bool = False,
    ) -> Union[List[Tuple], Tuple]:
        """
        Fetches data from the database. This can be used to fetch one or more rows from the DB.
        It automatically writes the fetch query based on the args provided. The condition dict
        should contain table column names as keys and the constraint values as values.

        Args:
            table (str): The table name to fetch data from.
            cols (List[str], optional): The list of columns to fetch. If this value is None then '*'
                is used in the query. Defaults to None.
            condition (Dict[str, Any], optional): Used to generate the where clause as needed. If
                this is empty then no where clause is used and all rows are fetched. Defaults to {}.
            single_row (bool, optional): Whether the query should return only one row or multiple.
                Defaults to False.

        Raises:
            NoConnection: If connection to the DB could not be established.

        Returns:
            Union[List[Tuple], Tuple]: A single row or a list containing multiple rows from the DB.
        """
        if cols is None:
            col_str = "*"
        else:
            col_str = ", ".join(cols)
        sql = f"SELECT {col_str} FROM {table}"
        if condition:
            condition_cols = condition.keys()
            condition_str = " AND ".join(f"{col} = %({col})s" for col in condition_cols)
            sql += f" WHERE {condition_str}"
        if not self.is_connected():
            self.connect()
        if self.conn is None:
            raise DBConnectionError("No connection to database.")
        with self.conn:
            with self.conn.cursor() as c:
                _LOG.info(f"Executing query: {sql}")
                c.execute(sql, condition)
                if single_row:
                    return_data = c.fetchone()
                else:
                    return_data = c.fetchall()
        return return_data

    def fetch_raw(
        self, sql: str, params: Union[List[Any], Dict[str, Any]] = [], single_row: bool = False
    ) -> Union[List[Tuple], Tuple]:
        with self.conn:
            with self.conn.cursor() as c:
                _LOG.info(f"Executing query: {sql}")
                c.execute(sql, params)
                if single_row:
                    return_data = c.fetchone()
                else:
                    return_data = c.fetchall()
        return return_data

    def insert_or_update_data(
        self,
        table: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        key_cols: List[str],
        update_xdb: bool = True,
    ):
        """
        Wrapper method to make insert or update an atomic operation. This is useful when it is not
        known whether data exists in the table. Using this function also has the benefit of not
        failing when a DB connection does not exist. If no DB connection is available this method
        ensures that once re-established the data will be properly handled. The data and key_cols
        parameters work the same way as they do for insert and update methods.

        Args:
            table (str): The table name to fetch data from.
            data (Union[Dict[str, Any], List[Dict[str, Any]]]): The data to insert/update. List of
                dicts updates multiple rows and a dict updates a single row.
            key_cols (List[str]): The columns part of the where clause. These must also be present
                in the data dict. Only used when insert fails and update is needed.
            update_xdb (bool, optional): Indicates whether to write data to xdb file if
                insert/update fails. Defaults to True.
        """
        try:
            try:
                self.insert_data(table, data, update_xdb=False)
            except psycopg2.IntegrityError:
                _LOG.info(f"Data already in {table}. Attempting to update {table}")
                self.update_data(table, data, key_cols, update_xdb=False)
        except (psycopg2.OperationalError, DBConnectionError) as ex:
            _LOG.error(f"{type(ex).__name__}: {str(ex)}")
            if update_xdb:
                _LOG.warning(f"Connection error. Data Will be written to file to be updated later.")
                self.write_xdb(
                    "insert_update", {"table": table, "data": data, "key_cols": key_cols}
                )
            else:
                raise

    def delete_data(self, table: str, condition: Dict[str, Any] = {}, update_xdb: bool = True):
        """
        Deletes data from a table in the database. The condition dict is used to generate the where
        clause and it should contain table column names as keys and the constraint values as values.
        If the condition dict is empty then all rows in the table will be deleted.

        Args:
            table (str): The table name to delete rows from.
            condition (Dict[str, Any], optional): Used to generate the where clause as needed. If
                this is empty then no where clause is used and all rows are deleted. Defaults to {}.
            update_xdb (bool, optional): Indicates whether to write data to xdb file if
                insert/update fails. Defaults to True.

        Raises:
            NoConnection: If connection to the DB could not be established.
        """
        sql = f"DELETE FROM {table}"
        if condition:
            condition_cols = condition.keys()
            condition_str = " AND ".join(f"{col} = %({col})s" for col in condition_cols)
            sql += f" WHERE {condition_str}"
        try:
            if not self.is_connected():
                self.connect()
            if self.conn is None:
                raise DBConnectionError("No connection to database.")
            with self.conn:
                with self.conn.cursor() as c:
                    _LOG.info(f"Executing query: {sql}")
                    c.execute(sql, condition)
            _LOG.info("Matching rows deleted successfully")
        except (psycopg2.OperationalError, DBConnectionError) as ex:
            _LOG.error(f"{type(ex).__name__}: {str(ex)}")
            if update_xdb:
                _LOG.warning(f"Connection error. Data Will be written to file to be updated later.")
                self.write_xdb("delete", {"table": table, "condition": condition})
            else:
                raise

    def write_xdb(self, txn_type: str, params: Dict[str, Any]):
        """
        Writes the data to a json file. This function is called when a DB transactions fails due to
        a connection error. The xdb file is updated with the txn_type and the required params for
        the transaction. This allows transactions to be properly executed later.

        Args:
            txn_type (str): The type of transaction such as insert,delete, or update.
            params (Dict[str, Any]): The parameters to pass to the transaction. Refer to each
                method to understand the params required.
        """

        data = {
            "txn_type": txn_type,
            "kwargs": params,
            "dbname": self.dbname,
            "dboptions": self.db_options,
            "dbkwargs": self.db_kwargs,
        }
        xdb_file = (
            self.xdb_dir / f"{os.getpid()}_txn_{dt.datetime.now().strftime('%Y%m%d_%H%S%M%f')}.xdb"
        )
        write_json_data(xdb_file, data, stage=True)
