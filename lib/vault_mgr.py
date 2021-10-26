#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Interface to vault credential manager
File: vault_mgr
Project: lib
File Created: Monday, 25th October 2021 8:50:09 pm
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
import hvac
from typing import List, Dict


class VaultMgr:
    """
    Allows other modules to read and list vault secrets.

    Attributes:
        client (hvac.Client): Client used to connect to vault and retrieve secrets.
        role_id (str): The role for the current application. Used to connect to vault
        secret_id (str): The secret id used in the connection.

    """

    KV_VERSION = 1
    MOUNT_POINT = "kv"

    def __init__(self, endpoint: str, role_id: str, secret_id: str) -> None:
        """
        Initializes the vault client and attempts to authenticate using role and secret and sets the
        default kv engine.

        Args:
            endpoint (str): The endpoint for the vault server.
            role_id (str): The app role id.
            secret_id (str): The secret id for the app role.
        """
        self.client = hvac.Client(endpoint)
        self.role_id = role_id
        self.secret_id = secret_id
        self._authenticate()
        self.client.secrets.kv.default_kv_version = self.KV_VERSION

    def _authenticate(self):
        """
        Checks for authentication and authenticates if client is not currently authenticated.
        """
        if self.client.is_authenticated():
            return
        self.client.auth.approle.login(role_id=self.role_id, secret_id=self.secret_id)

    def get_secret(self, path: str) -> Dict[str, str]:
        """
        Gets all kv pairs for a secret specified in the vault.

        Args:
            path (str): The path to the secret.

        Returns:
            dict: All kv pairs for the secret.
        """
        if not self.client.is_authenticated():
            self._authenticate()
        secret = self.client.secrets.kv.read_secret(path=path, mount_point=self.MOUNT_POINT)
        return secret["data"]

    def list_secrets(self, path: str = "") -> List[str]:
        """
        Lists all the secrets available at the current path. If no path is supplied defaults to the
        root mountpoint.

        Args:
            path (str): The path for the secrets. Defaults to "".

        Returns:
            list: Containing all secrets at the current path.
        """
        if not self.client.is_authenticated():
            self._authenticate()
        secrets = self.client.secrets.kv.list_secrets(path=path, mount_point=self.MOUNT_POINT)
        return secrets["data"]["keys"]
