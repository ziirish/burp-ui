#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import shutil

from setuptools import setup, find_packages

# only used to build the package
ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..')

if os.path.exists(os.path.join(ROOT, 'burpui', 'VERSION')):
    shutil.copyfile(os.path.join(ROOT, 'burpui', 'VERSION'), 'burpui_extra/VERSION')

readme = """
Burp-UI Meta package for extra requirements
"""

from burpui_extra import __author__, __author_email__, __description__, \
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
        'ujson',
        'redis',
        'Flask-Session==0.3.0'
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
