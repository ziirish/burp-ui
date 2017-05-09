#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import shutil
import subprocess

from setuptools import setup, find_packages

# only used to build the package
ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..')

if 'sdist' in sys.argv or 'bdist' in sys.argv:
    if not os.path.exists('burpui_agent'):
        os.makedirs('burpui_agent', mode=0o0755)
    if os.path.exists(os.path.join(ROOT, 'burpui', 'VERSION')):
        shutil.copyfile(os.path.join(ROOT, 'burpui', 'VERSION'), 'burpui_agent/VERSION')
    rev = 'stable'
    if os.path.exists(os.path.join(ROOT, '.git/HEAD')):
        try:
            branch = subprocess.check_output('sed s@^.*/@@g {}/.git/HEAD'.format(ROOT).split()).rstrip()
            ver = open(os.path.join('burpui_agent', 'VERSION')).read().rstrip()
            if branch and 'dev' in ver:
                rev = branch
            try:
                with open('burpui_agent/RELEASE', 'w') as f:
                    f.write(rev)
            except:
                pass
        except:
            pass
    find = subprocess.Popen(r'find burpui_agent-decoy -type l', shell=True, stdout=subprocess.PIPE)
    (out, _) = find.communicate()
    for decoy in out.splitlines():
        real = os.path.normpath(os.path.join(os.path.dirname(decoy),os.readlink(decoy)))
        # print '{} -> {}'.format(decoy, real)
        target = os.path.join('burpui_agent', re.sub(r'.*/burpui/', '', real))
        dirname = os.path.dirname(target)
        if not os.path.isdir(dirname):
            # print 'mkdir {}'.format(dirname)
            os.makedirs(dirname, mode=0o0755)
        # print 'cp -r {} {}'.format(real, target)
        if os.path.isdir(real):
            if os.path.exists(target):
                shutil.rmtree(target)
            shutil.copytree(real, target)
        else:
            shutil.copy(real, target)

    files = subprocess.Popen(r'find burpui_agent-decoy -type f', shell=True, stdout=subprocess.PIPE)
    (out, _) = files.communicate()
    for src in out.splitlines():
        dst = src.replace('burpui_agent-decoy', 'burpui_agent')
        dirname = os.path.dirname(dst)
        if not os.path.isdir(dirname):
            # print 'mkdir {}'.format(dirname)
            os.makedirs(dirname, mode=0o0755)
        shutil.copy(src, dst)

readme = """
Burp-UI Meta package for agent requirements
"""

from burpui_agent import __title__
from burpui_agent.desc import __author__, __author_email__, __description__, \
        __url__, __version__, __license__
name = __title__
author = __author__
author_email = __author_email__
description = __description__
url = __url__
version = __version__
license = __license__

datadir = os.path.join('share', 'burpui')
confdir = os.path.join(datadir, 'etc')

setup(
    name=name,
    packages=find_packages(exclude=['burpui_agent-decoy', 'burpui_agent-decoy.*']),
    version=version,
    description=description,
    long_description=readme,
    license=license,
    author=author,
    author_email=author_email,
    url=url,
    include_package_data=True,
    keywords='burp web ui backup monitoring',
    entry_points={
        'console_scripts': [
            'bui-agent=burpui_agent.__main__:agent',
        ],
    },
    data_files=[
        (confdir, [os.path.join(confdir, 'buiagent.sample.cfg')]),
    ],
    install_requires=[
        'gevent',
        'arrow==0.10.0',
        'tzlocal==1.4',
        'six==1.10.0',
        'pyOpenSSL==17.0.0',
        'configobj==5.0.6',
        'pyasn1==0.2.3',
        'cffi==1.10.0',
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
