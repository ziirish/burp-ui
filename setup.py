#!/usr/bin/env python
# coding: utf-8

import os
import sys
import re

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.version < '3':
    import codecs
    def u(x):
        return codecs.unicode_escape_decode(x)[0]
else:
    def u(x):
        return x

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

setup(
    name='burp-ui',
    version=open('VERSION').read().rstrip(),
    description=u('Burp-UI is a web-ui for burp backup written in python with Flask and jQuery/Bootstrap'),
    long_description=open('README.rst').read(),
    license=open('LICENSE').read(),
    author=u('Benjamin SANS (Ziirish)'),
    author_email=u('ziirish@ziirish.info'),
    url='http://git.ziirish.me/ziirish/burp-ui',
    keywords='burp web ui',
    packages=['burpui'],
    scripts=['bin/burp-ui'],
    py_modules=['burpui'],
    install_requires=['Flask==0.10.1', 'Flask-Login==0.2.11', 'Flask-WTF==0.10.0', 'WTForms==2.0.1'],
    extras_require={
        'ldap_authentication': ['simpleldap==0.8']
    },
    classifiers=[
        'Framework :: Flask',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: System :: Archiving :: Backup',
        'Topic :: System :: Monitoring'
    ]
)
