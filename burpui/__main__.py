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
import sys
import os
from argparse import ArgumentParser

# Try to load modules from our current env first
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))


def parse_args(mode=True, name=None):
    if not name:
        name = 'burp-ui'
    parser = ArgumentParser(prog=name)
    parser.add_argument('-v', '--verbose', dest='log', help='increase output verbosity (e.g., -vv is more verbose than -v)', action='count')
    parser.add_argument('-d', '--debug', dest='debug', help='enable debug mode', action='store_true')  # alias for -v
    parser.add_argument('-V', '--version', dest='version', help='print version and exit', action='store_true')
    parser.add_argument('-c', '--config', dest='config', help='configuration file', metavar='<CONFIG>')
    parser.add_argument('-l', '--logfile', dest='logfile', help='output logs in defined file', metavar='<FILE>')
    if mode:
        parser.add_argument('-m', '--mode', dest='mode', help='application mode (server, agent or celery)', metavar='<agent|server|celery>')

    options, unknown = parser.parse_known_args()
    if options.mode and options.mode != 'celery':
        options = parser.parse_args()

    if options.version:
        from burpui import __title__, __version__, __release__
        ver = '{}: v{}'.format(name or __title__, __version__)
        if options.log:
            ver = '{} ({})'.format(ver, __release__)
        print(ver)
        sys.exit(0)

    return options


def main():
    """
    Main function
    """
    options = parse_args(mode=True)

    if not options.mode or options.mode == 'server':
        server(options)
    elif options.mode == 'agent':
        agent(options)
    elif options.mode == 'celery':
        celery()
    else:
        print('Wrong mode!')
        sys.exit(1)


def server(options=None):
    from burpui import create_app, lookup_config

    if not options:
        options = parse_args(mode=False)

    conf = lookup_config(options.config)
    check_config(conf)

    server = create_app(conf, options.log, options.logfile, False, debug=options.debug)

    server.manual_run()


def agent(options=None):
    from burpui.agent import BUIAgent as Agent
    from burpui._compat import patch_json

    patch_json()

    if not options:
        options = parse_args(mode=False, name='bui-agent')

    conf = None
    if options.config:
        conf = options.config
    else:
        root = os.path.join(
            sys.prefix,
            'share',
            'burpui',
            'etc'
        )
        root2 = os.path.join(
            sys.prefix,
            'local',
            'share',
            'burpui',
            'etc'
        )
        root3 = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            '..',
            '..',
            '..',
            '..',
            'share',
            'burpui',
            'etc',
        )
        conf_files = [
            '/etc/burp/buiagent.cfg',
            os.path.join(root, 'buiagent.cfg'),
            os.path.join(root, 'buiagent.sample.cfg'),
            os.path.join(root2, 'buiagent.cfg'),
            os.path.join(root2, 'buiagent.sample.cfg'),
            os.path.join(root3, 'buiagent.cfg'),
            os.path.join(root3, 'buiagent.sample.cfg')
        ]
        for p in conf_files:
            if os.path.isfile(p):
                conf = p
                break

    check_config(conf)

    agent = Agent(conf, options.log, options.logfile, options.debug)
    agent.run()


def celery():
    from burpui import lookup_config

    parser = ArgumentParser('bui-celery')
    parser.add_argument('-c', '--config', dest='config', help='configuration file', metavar='<CONFIG>')
    parser.add_argument('-m', '--mode', dest='mode', help='application mode (server or agent)', metavar='<agent|server|worker>')

    options, unknown = parser.parse_known_args()

    conf = lookup_config(options.config)
    check_config(conf)

    env = os.environ
    env['BUI_CONFIG'] = conf

    args = [
        'celery',
        'worker',
        '-A',
        'celery_worker.celery'
    ]
    args += unknown

    os.execvpe('celery', args, env)


def check_config(conf):
    if not conf or not os.path.isfile(conf):
        raise IOError('File not found: \'{0}\''.format(conf))


if __name__ == '__main__':
    main()
