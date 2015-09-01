#!/usr/bin/env python
# coding: utf-8

import os
import os.path
import re
import sys

from setuptools import setup, find_packages


def readme():
    """
    Function used to skip the screenshots part
    """
    desc = ''
    cpt = 0
    with open('README.rst') as f:
        for l in f.readlines():
            if l.rstrip() == 'Screenshots':
                cpt += 1
            elif cpt > 0:
                cpt += 1
            if cpt > 7:
                cpt = 0
            if cpt > 0:
                continue
            desc += l
    return desc

with open(os.path.join(os.path.dirname(__file__), 'burpui', '__init__.py')) as f:
    data = f.read()

    name = re.search("__title__ *= *'(.*)'", data).group(1)
    author = re.search("__author__ *= *'(.*)'", data).group(1)
    author_email = re.search("__author_email__ *= *'(.*)'", data).group(1)
    description = re.search("__description__ *= *'(.*)'", data).group(1)
    url = re.search("__url__ *= *'(.*)'", data).group(1)

with open('requirements.txt', 'r') as f:
    requires = [x.strip() for x in f if x.strip()]

with open('test-requirements.txt', 'r') as f:
    test_requires = [x.strip() for x in f if x.strip()]

datadir = os.path.join('share', 'burpui', 'etc')
contrib = os.path.join('share', 'burpui', 'contrib')

setup(
    name=name,
    version=open('VERSION').read().rstrip(),
    description=description,
    long_description=readme(),
    license=open('LICENSE').read(),
    author=author,
    author_email=author_email,
    url=url,
    keywords='burp web ui',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'static': 'burpui/static/*',
        'templates': 'burpui/templates/*'
    },
    scripts=['bin/burp-ui', 'bin/bui-agent'],
    data_files=[
        (datadir, [os.path.join(datadir, 'burpui.sample.cfg')]),
        (datadir, [os.path.join(datadir, 'buiagent.sample.cfg')]),
        (os.path.join(contrib, 'centos'), ['contrib/centos/init.sh']),
        (os.path.join(contrib, 'debian'), ['contrib/debian/init.sh']),
        (os.path.join(contrib, 'gunicorn.d'), ['contrib/gunicorn.d/burp-ui'])
    ],
    install_requires=requires,
    extras_require={
        'ldap_authentication': ['ldap3']
    },
    tests_require=test_requires,
    classifiers=[
        'Framework :: Flask',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: System :: Archiving :: Backup',
        'Topic :: System :: Monitoring'
    ]
)
