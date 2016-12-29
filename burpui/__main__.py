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
    mname = name
    if not name:
        mname = 'burp-ui'
    parser = ArgumentParser(prog=mname)
    parser.add_argument('-v', '--verbose', dest='log', help='increase output verbosity (e.g., -vv is more verbose than -v)', action='count')
    parser.add_argument('-d', '--debug', dest='debug', help='enable debug mode', action='store_true')
    parser.add_argument('-V', '--version', dest='version', help='print version and exit', action='store_true')
    parser.add_argument('-c', '--config', dest='config', help='burp-ui configuration file', metavar='<CONFIG>')
    parser.add_argument('-l', '--logfile', dest='logfile', help='output logs in defined file', metavar='<FILE>')
    parser.add_argument('-i', '--migrations', dest='migrations', help='migrations directory', metavar='<MIGRATIONSDIR>')
    parser.add_argument('remaining', nargs=REMAINDER)
    if mode:
        parser.add_argument('-m', '--mode', dest='mode', help='application mode', metavar='<agent|server|celery|manage|legacy>')

    options, unknown = parser.parse_known_args()
    if mode and options.mode and options.mode not in ['celery', 'manage', 'server']:
        options = parser.parse_args()
        unknown = []

    if options.version:
        from burpui.desc import __title__, __version__, __release__
        ver = '{}: v{}'.format(name or __title__, __version__)
        if options.log:
            ver = '{} ({})'.format(ver, __release__)
        print(ver)
        sys.exit(0)

    return options, unknown


def main():
    """
    Main function
    """
    options, unknown = parse_args(mode=True)

    if not options.mode or options.mode == 'server':
        server(options, unknown)
    elif options.mode == 'agent':
        agent(options)
    elif options.mode == 'celery':
        celery()
    elif options.mode == 'manage':
        manage()
    elif options.mode == 'legacy':
        legacy(options, unknown)
    else:
        print('Wrong mode!')
        sys.exit(1)


def server(options=None, unknown=None):
    from burpui.utils import lookup_file

    if unknown is None:
        unknown = []
    if not options:
        options, unknown = parse_args(mode=False)
    env = os.environ

    if options.config:
        conf = lookup_file(options.config, guess=False)
    else:
        if 'BUI_CONFIG' in env:
            conf = env['BUI_CONFIG']
        else:
            conf = lookup_file()
    check_config(conf)

    if os.path.isdir('burpui'):
        env['FLASK_APP'] = 'burpui/cli.py'
    else:
        env['FLASK_APP'] = 'burpui.cli'
    env['BUI_CONFIG'] = conf
    env['BUI_VERBOSE'] = str(options.log)
    if options.logfile:
        env['BUI_LOGFILE'] = options.logfile
    if options.debug:
        env['BUI_DEBUG'] = '1'
        env['FLASK_DEBUG'] = '1'
    env['BUI_MODE'] = 'server'

    args = [
        'flask',
        'run'
    ]
    args += unknown
    args += [x for x in options.remaining if x != '--']

    os.execvpe(args[0], args, env)


def agent(options=None):
    from gevent import monkey
    from burpui.agent import BUIAgent as Agent
    from burpui.utils import lookup_file
    from burpui._compat import patch_json

    monkey.patch_all()
    patch_json()

    if not options:
        options, _ = parse_args(mode=False, name='bui-agent')

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
    parser.add_argument('-c', '--config', dest='config', help='burp-ui configuration file', metavar='<CONFIG>')
    parser.add_argument('-m', '--mode', dest='mode', help='application mode', metavar='<agent|server|worker|manage|legacy>')
    parser.add_argument('remaining', nargs=REMAINDER)

    options, unknown = parser.parse_known_args()
    env = os.environ

    if options.config:
        conf = lookup_file(options.config, guess=False)
    else:
        if 'BUI_CONFIG' in env:
            conf = env['BUI_CONFIG']
        else:
            conf = lookup_file()

    # make conf path absolute
    if not conf.startswith('/'):
        curr = os.getcwd()
        conf = os.path.join(curr, conf)

    check_config(conf)

    os.chdir(ROOT)

    env['BUI_MODE'] = 'celery'
    env['BUI_CONFIG'] = conf

    args = [
        'celery',
        'worker',
        '-A',
        'worker.celery'
    ]
    args += unknown
    args += [x for x in options.remaining if x != '--']

    os.execvpe(args[0], args, env)


def manage():
    from burpui.utils import lookup_file

    parser = ArgumentParser('bui-manage')
    parser.add_argument('-c', '--config', dest='config', help='burp-ui configuration file', metavar='<CONFIG>')
    parser.add_argument('-i', '--migrations', dest='migrations', help='migrations directory', metavar='<MIGRATIONSDIR>')
    parser.add_argument('-m', '--mode', dest='mode', help='application mode', metavar='<agent|server|worker|manage|legacy>')
    parser.add_argument('remaining', nargs=REMAINDER)

    options, unknown = parser.parse_known_args()
    env = os.environ

    if options.config:
        conf = lookup_file(options.config, guess=False)
    else:
        if 'BUI_CONFIG' in env:
            conf = env['BUI_CONFIG']
        else:
            conf = lookup_file()
    check_config(conf)

    if options.migrations:
        migrations = lookup_file(options.migrations, guess=False, directory=True, check=False)
    else:
        migrations = lookup_file('migrations', directory=True)

    env['BUI_MODE'] = 'manage'
    env['BUI_CONFIG'] = conf
    if migrations:
        env['BUI_MIGRATIONS'] = migrations
    if os.path.isdir('burpui'):
        env['FLASK_APP'] = 'burpui/cli.py'
    else:
        env['FLASK_APP'] = 'burpui.cli'

    args = [
        'flask'
    ]
    args += unknown
    args += [x for x in options.remaining if x != '--']

    os.execvpe(args[0], args, env)


def legacy(options=None, unknown=None):
    from burpui.utils import lookup_file

    if unknown is None:
        unknown = []
    if not options:
        options, unknown = parse_args(mode=False, name='burpui-legacy')
    env = os.environ

    if options.config:
        conf = lookup_file(options.config, guess=False)
    else:
        if 'BUI_CONFIG' in env:
            conf = env['BUI_CONFIG']
        else:
            conf = lookup_file()
    check_config(conf)

    env['BUI_MODE'] = 'legacy'
    env['BUI_CONFIG'] = conf
    if os.path.isdir('burpui'):
        env['FLASK_APP'] = 'burpui/cli.py'
    else:
        env['FLASK_APP'] = 'burpui.cli'
    env['BUI_VERBOSE'] = str(options.log)
    if options.logfile:
        env['BUI_LOGFILE'] = options.logfile
    if options.debug:
        env['BUI_DEBUG'] = '1'
        env['FLASK_DEBUG'] = '1'

    args = [
        'flask',
        'legacy'
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
