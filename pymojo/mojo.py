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

# ----- CLI CODE BELOW ----- #


def dict_merge(src, dest):
    """Helper function for merging config dictionaries"""
    # For each item in the source
    for key, value in src.items():
        # If the item is a dictionary, merge it
        if isinstance(value, dict):
            dict_merge(value, dest.setdefault(key, {}))
        # Otherwise, the destination takes the source value
        else:
            dest[key] = value
    return dest


def cli(args):
    """Run the command line client"""

    # Defaults
    config_files = [
        "/etc/mojo.yml",
        "{}/.mojo.yml".format(os.path.expanduser("~"))
    ]
    config = {"environments": {}, "default_environment": None}
    opts = {}
    default_opts = {
        "endpoint": "localhost",
        "port": 3000,
        "use_ssl": False,
        "verify": True,
        "user": None,
        "password": None
    }

    # User supplied additional config file?
    if args.config is not None:
        config_files.append(os.path.expanduser(args.config))

    # Merge the config dictionaries
    for config_file in config_files:
        try:
            config = dict_merge(yaml.load(open(config_file, 'r')), config)
        except IOError:
            pass

    # Some logic to determine if we have enough information to run
    # and also to load any preconfigured connection options

    # User supplied an environment name...
    if args.env is not None:
        # ...but it doesn't exist: error/exit.
        if args.env not in config["environments"]:
            print("The specified environment is not defined.")
            sys.exit(1)
        # ...and it is defined: "load" those settings.
        else:
            opts = config["environments"][args.env]
    # User did not supply an environment name...
    else:
        # ...but they have a default_environment...
        if config["default_environment"] is not None:
            # ...and that environment is defined: "load" those settings.
            if config["default_environment"] in config["environments"]:
                opts = config["environments"][config["default_environment"]]
            # ...but that env doesn't exist: error/exit.
            else:
                print("The default environment is not defined.")
                sys.exit(1)

    # Allow user to override settings from the CLI
    if args.endpoint is not None:
        opts["endpoint"] = args.endpoint
    if args.port is not None:
        opts["port"] = args.port
    if args.use_ssl is not None:
        opts["use_ssl"] = args.use_ssl
    if args.verify is not None:
        opts["verify"] = args.verify
    if args.user is not None:
        opts["user"] = args.user
    if args.password is not None:
        opts["password"] = args.password

    # Bring in any missing values at their defaults
    opts = dict_merge(opts, default_opts)

    # Route that action!
    if args.action == "list":
        list_scripts(opts)
    elif args.action == "show":
        show(opts, args)
    elif args.action == "run":
        run(opts, args)
    elif args.action == "reload":
        reload_jojo(opts)

    sys.exit(0)


def list_scripts(opts):
    """List available scripts"""
    mojo = Mojo(**opts)
    if mojo.auth and mojo.unauthorized:
        print("Authentication failed")
    else:
        for script in sorted(mojo.scripts):
            print(script)


def show(opts, args):
    """Show script details"""
    mojo = Mojo(**opts)
    script = mojo.get_script(args.script)

    if mojo.auth and mojo.unauthorized:
        print("Authentication failed")
    else:
        print("Name: {}".format(script["name"]))
        print("Lock: {}".format(script["lock"]))
        print("Filename: {}".format(script["filename"]))
        print("Description: {}".format(script["description"]))
        if "params" in script:
            print("Parameters:")
            for param in sorted(script["params"]):
                print(" {}: {}".format(param["name"], param["description"]))

        if "filtered_params" in script:
            print("Filtered parameters:")
            for param in script["filtered_params"]:
                print(" ", param)


def run(opts, args):
    """Run a script"""
    mojo = Mojo(**opts)

    # Parse CLI-given parameters
    params = {}
    for param in args.params:
        broken = param.split("=")
        params[broken[0]] = broken[1]

    resp = mojo.run(args.script, params)

    if mojo.auth and mojo.unauthorized:
        print("Authentication failed")
    else:
        print("Status Code: {}".format(resp.status_code))

        print("Headers:")
        for header in resp.headers:
            print(" {}: {}".format(header, resp.headers[header]))

        j = resp.json()
        print("Script return code: {}".format(j["retcode"]))
        print("Stderr: {}".format(j["stderr"]))
        print("Stdout: {}".format(j["stdout"]))


def reload_jojo(opts):
    """Reload the Jojo"""
    mojo = Mojo(**opts)
    result = mojo.reload()

    if result:
        print("Reload successful!")
    elif not result:
        print("Authentication failed")
    elif type(result) == int:
        print(
            "The Jojo responded with an unexpected status code: {code}".
            format(code=result)
        )


def create_argument_parser():

    parser = argparse.ArgumentParser(description="Mojo command line client")
    parser.add_argument(
        "-c",
        "--config",
        dest="config",
        default=None,
        help="A YAML configuration file"
    )
    parser.add_argument(
        "-e",
        "--endpoint",
        dest="endpoint",
        default=None,
        help="The host to connect to a Jojo instance on"
    )
    parser.add_argument(
        "-p",
        "--port",
        dest="port",
        default=None,
        help="The port Jojo is listening on"
    )
    parser.add_argument(
        "-s",
        "--ssl",
        action="store_true",
        dest="use_ssl",
        default=None,
        help="Use SSL"
    )
    parser.add_argument(
        "-i",
        "--ignore-warnings",
        action="store_false",
        dest="verify",
        default=None,
        help="Ignore SSL certificate security warnings"
    )
    parser.add_argument(
        "-u",
        "--user",
        dest="user",
        default=None,
        help="The user to authenticate with"
    )
    parser.add_argument(
        "-w",
        "--password",
        dest="password",
        default=None,
        help="The password to authenticate with"
    )
    parser.add_argument(
        "-n",
        "--environment",
        dest="env",
        default=None,
        help="The name of the configured environment to control"
    )
    parser.add_argument(
        "action",
        choices=["list", "show", "run", "reload"],
        help="The action you want to take"
    )
    parser.add_argument(
        "script",
        nargs="?",
        default=None,
        help="For 'show' and 'run' commands, this is the relevant script"
    )
    parser.add_argument(
        "params",
        nargs=argparse.REMAINDER,
        help="Params to pass through the 'run' command in 'key1=value' format"
    )
    return parser


def main():
    """CLI client main entry point"""
    parser = create_argument_parser()
    cli(parser.parse_args())

if __name__ == "__main__":
    main()
