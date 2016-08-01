#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Burp-UI is a web-ui for burp backup written in python with Flask and
jQuery/Bootstrap

.. module:: burpui.manage
    :platform: Unix
    :synopsis: Burp-UI Manager app.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>
"""
import os
import sys

from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

# Try to load modules from our current env first
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))


def create_manager():
    from burpui import create_app

    conf = os.getenv('BUI_CONFIG')
    app = create_app(conf)
    manager = Manager(app)

    if app.config['WITH_SQL']:
        from burpui.ext.sql import db
        mig_dir = os.getenv('BUI_MIGRATIONS')
        if mig_dir:
            migrate = Migrate(app, db, mig_dir)
        else:
            migrate = Migrate(app, db)

        manager.add_command('db', MigrateCommand)
    else:
        migrate = None

    return manager, migrate, app

manager, migrate, app = create_manager()


@manager.command
def create_user(name, backend='BASIC', password=None, ask=False):
    print('[*] Adding \'{}\' user...'.format(name))
    try:
        handler = getattr(app, 'uhandler')
    except AttributeError:
        handler = None

    if not handler or len(handler.backends) == 0 or \
            backend not in handler.backends:
        print('[!] No authentication backend found')
        sys.exit(1)

    back = handler.backends[backend]

    if back.add_user is False:
        print("[!] The '{}' backend does not support user "
              "creation".format(backend))
        sys.exit(2)

    if not password:
        if ask:
            import getpass
            password = getpass.getpass()
            confirm = getpass.getpass('Confirm: ')
            if password != confirm:
                print("[!] Passwords missmatch")
                sys.exit(3)
        else:
            import random

            alphabet = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRST" \
                       "UVWXYZ"
            pw_length = 8
            mypw = ""

            for i in range(pw_length):
                next_index = random.randrange(len(alphabet))
                mypw += alphabet[next_index]
            password = mypw
            print('[+] Generated password: {}'.format(password))

    success, _, _ = back.add_user(name, password)
    print('[+] Success: {}'.format(success))


if __name__ == '__main__':
    manager.run()
