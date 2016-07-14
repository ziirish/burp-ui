#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

# Try to load modules from our current env first
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))


def create_manager():
    from burpui import create_app

    config = os.getenv('BUI_CONFIG')
    app = create_app(config)
    db = app.db

    if db:
        migrate = Migrate(app, db)
    else:
        migrate = None

    manager = Manager(app)

    if db:
        manager.add_command('db', MigrateCommand)

    return manager, migrate, app

manager, migrate, app = create_manager()


@manager.command
def create_user(name, backend='BASIC', password=None):
    print('[*] Adding \'{}\' user...'.format(name))
    try:
        handler = getattr(app, 'uhandler')
    except AttributeError:
        handler = None

    if not handler or len(handler.backends) == 0:
        print('No authentication backend found')
        sys.exit(1)

    back = None
    for bck in handler.backends:
        if bck.name == backend:
            back = bck

    if not back:
        print('No authentication backend found')
        sys.exit(1)

    if back.add_user is False:
        print("The '{}' backend does not support user creation".format(backend))
        sys.exit(2)

    if not password:
        import random

        alphabet = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
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
