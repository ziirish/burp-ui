#!/usr/bin/env python
# -*- coding: utf8 -*-
import os
from optparse import OptionParser

from burpui import app, bui

if __name__ == '__main__':
    """
    Main function
    """
    parser = OptionParser()
    parser.add_option('-v', '--verbose', dest='log', help='verbose output', action='store_true')
    parser.add_option('-c', '--config', dest='config', help='configuration file', metavar='CONFIG')

    (options, args) = parser.parse_args()
    d = options.log
    app.config['DEBUG'] = d

    if options.config:
        conf = options.config
    else:
        conf = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'burpui.cfg')

    app.config['CFG'] = conf

    bui.setup(conf)
    bui.run(d)

