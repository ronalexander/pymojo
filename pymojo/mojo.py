"""A class and CLI client to interact with a Pyjojo instance"""
import argparse
import base64
import json
import os
import requests
import sys
import yaml


class Mojo(object):
    """A class used to interact with a Pyjojo instance"""
    def __init__(self, **kwargs):
        """Constructs a Mojo by connecting to a Jojo and caching its scripts"""
        # Transform some options into connection data
        url = "http://{}"
        if kwargs.get("use_ssl", False):
            url = "https://{}"

        self.endpoint = url.format(
            "{}:{}".format(
                kwargs.get("endpoint", "localhost"),
                kwargs.get("port", 3000)
            )
        )

        self.verify = kwargs.get("verify", True)
        self.user = kwargs.get("user", None)
        self.password = kwargs.get("password", None)

        if (self.user is not None) & (self.password is not None):
            self.auth = True
        else:
            self.auth = False

        self.unauthorized = False

        # Get the script lexicon from the Jojo and cache it
        self.scripts = self.__get_scripts()

    def __call(self, path, method="GET", data=""):
        """Makes a call to a Jojo"""
        session = requests.Session()
        headers = {"Content-Type": "application/json"}

        if self.auth:
            headers["Authorization"] = "Basic {}".format(base64.b64encode(
                "{}:{}".format(self.user, self.password))
            )

        req = requests.Request(
            method,
            "{}{}".format(self.endpoint, path),
            data=data,
            headers=headers
        ).prepare()

        response = session.send(req, verify=self.verify)
        if response.status_code == 401:
            self.unauthorized = True

        return response

    def __get_scripts(self):
        """Gets a collection of scripts that live on the Jojo"""
        resp = self.__call("/scripts", method="GET")
        if resp.status_code == 200:
            return resp.json()['scripts']
        elif resp.status_code == 401:
            self.unauthorized = True
            resp.raise_for_status()

        return {}

    def reload(self):
        """Reloads the Jojo's script cache, then stashes that data in the
           Mojo"""
        response = self.__call("/reload", method="POST")

        if response.status_code == 200:
            self.scripts = self.__get_scripts()
            return True
        elif response.status_code == 401:
            return False
        else:
            return None

    def get_script(self, name, use_cache=True):
        """Gets data about a script in the Jojo, from the cache or from the
           Jojo"""
        if use_cache:
            if name in self.scripts:
                return self.scripts[name]
            else:
                return None
        else:
            resp = self.__call("/scripts/{}".format(name), method="GET")
            if resp.status_code == 200:
                self.scripts[name] = resp.json()['script']
                return self.scripts[name]
            else:
                return None

    def run(self, name, params=None):
        """Runs the named script with the given parameters"""
        data = None
        if params is not None:
            data = json.dumps(params)

        return self.__call(
            "/scripts/{}".format(name), method="POST", data=data
        )
