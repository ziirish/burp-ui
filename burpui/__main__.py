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
import os
import sys

from argparse import ArgumentParser, REMAINDER

ROOT = os.path.dirname(os.path.realpath(__file__))
# Try to load modules from our current env first
sys.path.insert(0, os.path.join(ROOT, '..'))


def parse_args(mode=True, name=None):
    if not name:
        name = 'burp-ui'
    parser = ArgumentParser(prog=name)
    parser.add_argument('-v', '--verbose', dest='log', help='increase output verbosity (e.g., -vv is more verbose than -v)', action='count')
    parser.add_argument('-d', '--debug', dest='debug', help='enable debug mode', action='store_true')  # alias for -v
    parser.add_argument('-V', '--version', dest='version', help='print version and exit', action='store_true')
    parser.add_argument('-c', '--config', dest='config', help='configuration file', metavar='<CONFIG>')
    parser.add_argument('-l', '--logfile', dest='logfile', help='output logs in defined file', metavar='<FILE>')
    parser.add_argument('-i', '--migrations', dest='migrations', help='migrations directory', metavar='<MIGRATIONSDIR>')
    parser.add_argument('remaining', nargs=REMAINDER)
    if mode:
        parser.add_argument('-m', '--mode', dest='mode', help='application mode', metavar='<agent|server|celery|manage>')

    options, unknown = parser.parse_known_args()
    if mode and options.mode and options.mode not in ['celery', 'manage']:
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
    elif options.mode == 'manage':
        manage()
    else:
        print('Wrong mode!')
        sys.exit(1)


def server(options=None):
    from burpui import create_app
    from burpui.utils import lookup_file

    if not options:
        options = parse_args(mode=False)

    if options.config:
        conf = lookup_file(options.config, guess=False)
    else:
        conf = lookup_file()
    check_config(conf)

    server = create_app(conf, options.log, options.logfile, False, debug=options.debug)

    server.manual_run()


def agent(options=None):
    from gevent import monkey
    from burpui.agent import BUIAgent as Agent
    from burpui.utils import lookup_file
    from burpui._compat import patch_json

    monkey.patch_all()
    patch_json()

    if not options:
        options = parse_args(mode=False, name='bui-agent')

    conf = ['buiagent.cfg', 'buiagent.sample.cfg']
    if options.config:
        conf = lookup_file(options.config, guess=False)
    else:
        conf = lookup_file(conf)
    check_config(conf)

    agent = Agent(conf, options.log, options.logfile, options.debug)
    agent.run()


def celery():
    from burpui.utils import lookup_file

    parser = ArgumentParser('bui-celery')
    parser.add_argument('-c', '--config', dest='config', help='configuration file', metavar='<CONFIG>')
    parser.add_argument('-m', '--mode', dest='mode', help='application mode', metavar='<agent|server|worker|manage>')
    parser.add_argument('remaining', nargs=REMAINDER)

    options, unknown = parser.parse_known_args()

    if options.config:
        conf = lookup_file(options.config, guess=False)
    else:
        conf = lookup_file()
    check_config(conf)

    # make conf path absolute
    if not conf.startswith('/'):
        curr = os.getcwd()
        conf = os.path.join(curr, conf)

    os.chdir(ROOT)

    env = os.environ
    env['BUI_CONFIG'] = conf

    args = [
        'celery',
        'worker',
        '-A',
        'celery_worker.celery'
    ]
    args += unknown
    args += [x for x in options.remaining if x != '--']

    os.execvpe(args[0], args, env)


def manage():
    from burpui.utils import lookup_file

    parser = ArgumentParser('bui-manage')
    parser.add_argument('-c', '--config', dest='config', help='configuration file', metavar='<CONFIG>')
    parser.add_argument('-i', '--migrations', dest='migrations', help='migrations directory', metavar='<MIGRATIONSDIR>')
    parser.add_argument('-m', '--mode', dest='mode', help='application mode', metavar='<agent|server|worker|manage>')
    parser.add_argument('remaining', nargs=REMAINDER)

    options, unknown = parser.parse_known_args()

    if options.config:
        conf = lookup_file(options.config, guess=False)
    else:
        conf = lookup_file()
    check_config(conf)

    if options.migrations:
        migrations = lookup_file(options.migrations, guess=False, directory=True, check=False)
    else:
        migrations = lookup_file('migrations', directory=True)

    env = os.environ
    env['BUI_CONFIG'] = conf
    if migrations:
        env['BUI_MIGRATIONS'] = migrations

    args = [
        sys.executable,
        os.path.join(ROOT, 'manage.py'),
    ]
    args += unknown
    args += [x for x in options.remaining if x != '--']

    os.execvpe(args[0], args, env)


def check_config(conf):
    if not conf:
        raise IOError('No configuration file found')
    if not os.path.isfile(conf):
        raise IOError('File does not exist: \'{0}\''.format(conf))


if __name__ == '__main__':
    main()
