#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import shutil
import subprocess

from setuptools import setup, find_packages

# only used to build the package
CWD = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..')

raw_requirements = [
    'gevent',
    'arrow',
    'tzlocal',
    'six',
    'pyOpenSSL',
    'configobj',
    'pyasn1',
    'cffi',
]
requirements = []

if 'sdist' in sys.argv or 'bdist' in sys.argv:
    try:
        with open(os.path.join(ROOT, 'requirements.txt'), 'r') as req:
            for line in req.readlines():
                line = line.rstrip()
                for i, look in enumerate(list(raw_requirements)):
                    if re.match(r'{}(=><)?'.format(look), line, re.IGNORECASE):
                        requirements.append(line)
                        del raw_requirements[i]
                        break
        requirements += raw_requirements
    except OSError:
        pass
    if requirements:
        try:
            with open(os.path.join(CWD, 'requirements.txt'), 'w') as req:
                req.write('\n'.join(requirements))
        except OSError:
            pass
    if not os.path.exists('burpui_agent'):
        os.makedirs('burpui_agent', mode=0o0755)
    if os.path.exists(os.path.join(ROOT, 'burpui', 'VERSION')):
        shutil.copyfile(os.path.join(ROOT, 'burpui', 'VERSION'), 'burpui_agent/VERSION')
    rev = 'stable'
    ci = os.getenv('CI')
    commit = os.getenv('CI_COMMIT_SHA')
    if not ci and os.path.exists(os.path.join(ROOT, '.git/HEAD')):
        try:
            branch = subprocess.check_output('sed s@^.*/@@g {}/.git/HEAD'.format(ROOT).split()).rstrip()
            ver = open(os.path.join('burpui_agent', 'VERSION')).read().rstrip()
            if branch and 'dev' in ver:
                rev = branch
            try:
                with open('burpui_agent/RELEASE', 'wb') as f:
                    f.write(rev)
            except:
                pass
        except:
            pass
    elif ci:
        try:
            ver = open(os.path.join('burpui_agent', 'VERSION')).read().rstrip()
            if 'dev' in ver:
                rev = commit
            try:
                with open('burpui_agent/RELEASE', 'wb') as f:
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
        target = os.path.join(b'burpui_agent', re.sub(b'.*/burpui/', b'', real))
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
        dst = src.replace(b'burpui_agent-decoy', b'burpui_agent')
        dirname = os.path.dirname(dst)
        if not os.path.isdir(dirname):
            # print 'mkdir {}'.format(dirname)
            os.makedirs(dirname, mode=0o0755)
        shutil.copy(src, dst)

if not requirements:
    try:
        with open(os.path.join(CWD, 'requirements.txt'), 'r') as req:
            requirements = [x.rstrip() for x in req.readlines()]
    except OSError:
        pass

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
    install_requires=requirements,
    classifiers=[
        'Framework :: Flask',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
        'Topic :: System :: Archiving :: Backup',
        'Topic :: System :: Monitoring',
    ]
)
