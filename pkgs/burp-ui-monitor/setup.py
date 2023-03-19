#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import shutil
import subprocess
import sys

from setuptools import find_packages, setup

# only used to build the package
CWD = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..")

raw_requirements = [
    "trio",
    "arrow",
    "tzlocal",
    "pyOpenSSL",
    "configobj",
]
requirements = []

if "sdist" in sys.argv or "bdist" in sys.argv:
    try:
        with open(os.path.join(ROOT, "requirements.txt"), "r") as req:
            for line in req.readlines():
                line = line.rstrip()
                for i, look in enumerate(list(raw_requirements)):
                    if re.match(r"{}(=><)?".format(look), line, re.IGNORECASE):
                        requirements.append(line)
                        del raw_requirements[i]
                        break
        requirements += raw_requirements
    except OSError:
        pass
    if requirements:
        try:
            with open(os.path.join(CWD, "requirements.txt"), "w") as req:
                req.write("\n".join(requirements))
        except OSError:
            pass
    if not os.path.exists("burpui_monitor"):
        os.makedirs("burpui_monitor", mode=0o0755)
    if os.path.exists(os.path.join(ROOT, "burpui", "VERSION")):
        shutil.copyfile(
            os.path.join(ROOT, "burpui", "VERSION"), "burpui_monitor/VERSION"
        )
    rev = "stable"
    ci = os.getenv("CI")
    commit = os.getenv("CI_COMMIT_SHA")
    if not ci and os.path.exists(os.path.join(ROOT, ".git/HEAD")):
        try:
            branch = subprocess.check_output(
                "sed s@^.*/@@g {}/.git/HEAD".format(ROOT).split()
            ).rstrip()
            ver = open(os.path.join("burpui_monitor", "VERSION")).read().rstrip()
            if branch and "dev" in ver:
                rev = branch
            try:
                with open("burpui_monitor/RELEASE", "wb") as f:
                    f.write(rev)
            except:
                pass
        except:
            pass
    elif ci:
        try:
            ver = open(os.path.join("burpui_monitor", "VERSION")).read().rstrip()
            if "dev" in ver:
                rev = commit
            try:
                with open("burpui_monitor/RELEASE", "wb") as f:
                    f.write(rev)
            except:
                pass
        except:
            pass
    find = subprocess.Popen(
        r"find burpui_monitor-decoy -type l", shell=True, stdout=subprocess.PIPE
    )
    (out, _) = find.communicate()
    for decoy in out.splitlines():
        real = os.path.normpath(
            os.path.join(os.path.dirname(decoy), os.readlink(decoy))
        ).decode("utf-8")
        # print '{} -> {}'.format(decoy, real)
        target = os.path.join("burpui_monitor", re.sub(r".*/burpui/", "", real))
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

    files = subprocess.Popen(
        r"find burpui_monitor-decoy -type f", shell=True, stdout=subprocess.PIPE
    )
    (out, _) = files.communicate()
    for src in out.splitlines():
        src = src.decode("utf-8")
        dst = src.replace("burpui_monitor-decoy", "burpui_monitor")
        dirname = os.path.dirname(dst)
        if not os.path.isdir(dirname):
            # print 'mkdir {}'.format(dirname)
            os.makedirs(dirname, mode=0o0755)
        shutil.copy(src, dst)

if not requirements:
    try:
        with open(os.path.join(CWD, "requirements.txt"), "r") as req:
            requirements = [x.rstrip() for x in req.readlines()]
    except OSError:
        pass

readme = """
Burp-UI Meta package for monitor requirements
"""

from burpui_monitor import __title__
from burpui_monitor.desc import (
    __author__,
    __author_email__,
    __description__,
    __license__,
    __url__,
    __version__,
)

name = __title__
author = __author__
author_email = __author_email__
description = __description__
url = __url__
version = __version__
license = __license__

datadir = os.path.join("share", "burpui")
confdir = os.path.join(datadir, "etc")

setup(
    name=name,
    packages=find_packages(exclude=["burpui_monitor-decoy", "burpui_monitor-decoy.*"]),
    version=version,
    description=description,
    long_description=readme,
    license=license,
    author=author,
    author_email=author_email,
    url=url,
    include_package_data=True,
    keywords="burp web ui backup monitoring",
    entry_points={
        "console_scripts": [
            "bui-monitor=burpui_monitor.__main__:monitor",
        ],
    },
    data_files=[
        (confdir, [os.path.join(confdir, "buimonitor.sample.cfg")]),
    ],
    install_requires=requirements,
    classifiers=[
        "Intended Audience :: System Administrators",
        "Natural Language :: English",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Topic :: System :: Archiving :: Backup",
        "Topic :: System :: Monitoring",
    ],
)
