#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
Burp-UI is a web-ui for burp backup written in python with Flask and
jQuery/Bootstrap

.. module:: burpui.__main__
    :platform: Unix
    :synopsis: Burp-UI main module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>
"""
import logging
import os
import sys
from argparse import ArgumentParser

ROOT = os.path.dirname(os.path.realpath(__file__))
# Try to load modules from our current env first
sys.path.insert(0, os.path.join(ROOT, ".."))

from burpui_agent.tools.logging import logger

logger.init_logger(config=dict(level=logging.CRITICAL))


def parse_args(name=None):
    mname = name
    if not name:
        mname = "bui-agent"
    parser = ArgumentParser(prog=mname)
    parser.add_argument(
        "-v",
        "--verbose",
        dest="log",
        help="increase output verbosity (e.g., -vv is more verbose than -v)",
        action="count",
    )
    parser.add_argument(
        "-V",
        "--version",
        dest="version",
        help="print version and exit",
        action="store_true",
    )
    parser.add_argument(
        "-c",
        "--config",
        dest="config",
        help="burp-ui configuration file",
        metavar="<CONFIG>",
    )
    parser.add_argument(
        "-l",
        "--logfile",
        dest="logfile",
        help="output logs in defined file",
        metavar="<FILE>",
    )

    options = parser.parse_args()

    if options.version:
        from burpui_agent import __title__
        from burpui_agent.desc import __release__, __version__

        ver = "{}: v{}".format(mname or __title__, __version__)
        if options.log:
            ver = "{} ({})".format(ver, __release__)
        print(ver)
        sys.exit(0)

    return options


def main():
    """
    Main function
    """
    options = parse_args()
    agent(options)


def agent(options=None):
    import trio
    from burpui_agent._compat import patch_json
    from burpui_agent.engines.agent import BUIAgent as Agent
    from burpui_agent.utils import lookup_file

    patch_json()

    if not options:
        options = parse_args(name="bui-agent")

    conf = ["buiagent.cfg", "buiagent.sample.cfg"]
    if options.config:
        conf = lookup_file(options.config, guess=False)
    else:
        conf = lookup_file(conf)
    check_config(conf)

    agent = Agent(conf, options.log, options.logfile)
    trio.run(agent.run)


def check_config(conf):
    if not conf:
        raise IOError("No configuration file found")
    if not os.path.isfile(conf):
        raise IOError("File does not exist: '{0}'".format(conf))


if __name__ == "__main__":
    main()
