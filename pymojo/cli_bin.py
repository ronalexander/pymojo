"""The executable component of the Mojo command line client"""
import argparse

import pymojo.cli as cli


def create_argument_parser():
    """Builds and returns an argument parser for this application"""
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
        "-g",
        "--group",
        dest="group",
        default=None,
        help="The group of Jojo instances to perform actions")
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
        default=None, help="Use SSL"
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
        "-b",
        "--list-boolean",
        choices=["and", "or", "not"],
        dest="boolean",
        default=None,
        help="""When listing with a script tag filter, this specifies the
             boolean operator to use describing the tag filter.
             """
    )
    parser.add_argument(
        "-t",
        "--tags",
        dest="tags",
        default=None,
        help="""When listing with a script tag filter, this specifies the list
             of tags to filter by. Also see the -b flag.
             """
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
    cli.cli(parser.parse_args())


if __name__ == "__main__":
    main()
