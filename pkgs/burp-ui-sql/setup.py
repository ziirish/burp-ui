#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from setuptools import setup, find_packages

ROOT=os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..')
## Try to load modules from our current env first
#sys.path.insert(0, ROOT)

readme = """
Burp-UI Meta package for SQL requirements
"""

from burpui_sql import __author__, __author_email__, __description__, \
        __url__, __title__, __version__, __license__
name = __title__
author = __author__
author_email = __author_email__
description = __description__
url = __url__
version = __version__
license = __license__

setup(
    name=name,
    packages=find_packages(),
    version=version,
    description=description,
    long_description=readme,
    license=license,
    author=author,
    author_email=author_email,
    url=url,
    keywords='burp web ui backup monitoring',
    install_requires=[
        'burp-ui>={}'.format(version),
        'Flask-SQLAlchemy',
        'Flask-Migrate>=2.0.1',
        'sqlalchemy-utils'
    ],
    classifiers=[
        'Framework :: Flask',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Topic :: System :: Archiving :: Backup',
        'Topic :: System :: Monitoring',
    ]
)
