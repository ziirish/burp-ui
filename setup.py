#!/usr/bin/env python
# coding: utf-8

import os
import os.path
import re
import sys

from subprocess import check_output, call
from distutils import log
from distutils.core import Command
from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.sdist import sdist
from setuptools.command.install import install
from setuptools.command.bdist_egg import bdist_egg
from setuptools.command.egg_info import egg_info

ROOT=os.path.join(os.path.dirname(os.path.realpath(__file__)))


class DevelopWithBuildStatic(develop):
    def install_for_development(self):
        self.run_command('build_static')
        return develop.install_for_development(self)


class EggWithBuildStatic(egg_info):
    def initialize_options(self):
        self.run_command('build_static')
        return egg_info.initialize_options(self)


class BdistWithBuildStatic(bdist_egg):
    def initialize_options(self):
        self.run_command('build_static')
        return bdist_egg.initialize_options(self)


class SdistWithBuildStatic(sdist):
    def make_distribution(self):
        self.run_command('build_static')
        return sdist.make_distribution(self)


class PyTest(Command):
    user_options = []
    description = "Run tests"
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        errno = call(['make', 'test'])
        raise SystemExit(errno)


class BuildStatic(Command):
    user_options = []
    description = "Install bower dependencies"
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        os.chdir(ROOT)
        log.info("getting revision number")
        try:
            branch = check_output('sed s@^.*/@@g .git/HEAD'.split()).rstrip()
            ver = open(os.path.join('burpui', 'VERSION')).read().rstrip()
            if branch and 'dev' in ver:
                rev = branch
            else:
                rev = 'stable'
            try:
                with open('burpui/RELEASE', 'w') as f:
                    f.write(rev)
            except:
                pass
        except:
            pass
        log.info("running [bower install]")
        try:
            check_output(['bower', 'install'])
        except Exception as e:
            log.warn('Bower error: {}'.format(str(e)))
        # Not sure bower was a great idea...
        keep = [
            'burpui/static/vendor/bootswatch/slate/bootstrap.min.css',
            'burpui/static/vendor/bootswatch/fonts/glyphicons-halflings-regular.eot',
            'burpui/static/vendor/bootswatch/fonts/glyphicons-halflings-regular.svg',
            'burpui/static/vendor/bootswatch/fonts/glyphicons-halflings-regular.ttf',
            'burpui/static/vendor/bootswatch/fonts/glyphicons-halflings-regular.woff',
            'burpui/static/vendor/bootswatch/fonts/glyphicons-halflings-regular.woff2',
            'burpui/static/vendor/nvd3/build/nv.d3.min.css',
            'burpui/static/vendor/datatables/media/css/dataTables.bootstrap.min.css',
            'burpui/static/vendor/jquery.fancytree/dist/skin-bootstrap/ui.fancytree.min.css',
            'burpui/static/vendor/bootstrap-switch/dist/css/bootstrap3/bootstrap-switch.min.css',
            'burpui/static/vendor/ui-select/dist/select.min.css',
            'burpui/static/vendor/jquery/dist/jquery.min.js',
            'burpui/static/vendor/jquery-ui/jquery-ui.min.js',
            'burpui/static/vendor/bootstrap/dist/js/bootstrap.min.js',
            'burpui/static/vendor/typeahead.js/dist/typeahead.bundle.min.js',
            'burpui/static/vendor/d3/d3.min.js',
            'burpui/static/vendor/nvd3/build/nv.d3.min.js',
            'burpui/static/vendor/datatables/media/js/jquery.dataTables.min.js',
            'burpui/static/vendor/datatables/media/js/dataTables.bootstrap.min.js',
            'burpui/static/vendor/datatables-responsive/js/dataTables.responsive.js',
            'burpui/static/vendor/jquery.fancytree/dist/jquery.fancytree-all.min.js',
            'burpui/static/vendor/jquery-file-download/src/Scripts/jquery.fileDownload.js',
            'burpui/static/vendor/lodash/dist/lodash.min.js',
            'burpui/static/vendor/angular/angular.min.js',
            'burpui/static/vendor/angular-route/angular-route.min.js',
            'burpui/static/vendor/angular-sanitize/angular-sanitize.min.js',
            'burpui/static/vendor/angular-resource/angular-resource.min.js',
            'burpui/static/vendor/angular-animate/angular-animate.min.js',
            'burpui/static/vendor/bootstrap-switch/dist/js/bootstrap-switch.min.js',
            'burpui/static/vendor/angular-bootstrap-switch/dist/angular-bootstrap-switch.min.js',
            'burpui/static/vendor/ui-select/dist/select.min.js',
            'burpui/static/vendor/angular-strap/dist/angular-strap.min.js',
            'burpui/static/vendor/angular-strap/dist/angular-strap.tpl.min.js',
            'burpui/static/vendor/angular-onbeforeunload/build/angular-onbeforeunload.js',
        ]
        dirlist = []
        for dirname, subdirs, files in os.walk('burpui/static/vendor'):
            for filename in files:
                path = os.path.join(dirname, filename)
                # _, ext = os.path.splitext(path)
                if os.path.isfile(path) and path not in keep:  # and ext != '.map':
                    os.unlink(path)
                elif os.path.isdir(path):
                    dirlist.append(path)
        dirlist.sort(reverse=True)
        for d in dirlist:
            if os.path.isdir(d) and not os.listdir(d):
                os.rmdir(d)


class CustomInstall(install):
    def run(self):
        self.run_command('build_static')
        install.run(self)

def readme():
    """
    Function used to skip the screenshots part
    """
    desc = ''
    cpt = 0
    skip = False
    with open(os.path.join(ROOT, 'README.rst')) as f:
        for l in f.readlines():
            if l.rstrip() == 'Screenshots':
                skip = True
            if skip:
                cpt += 1
            if cpt > 7:
                skip = False
            if skip:
                continue
            desc += l
    return desc

with open(os.path.join(ROOT, 'burpui', '__init__.py')) as f:
    data = f.read()

    name = re.search("__title__ *= *'(.*)'", data).group(1)
    author = re.search("__author__ *= *'(.*)'", data).group(1)
    author_email = re.search("__author_email__ *= *'(.*)'", data).group(1)
    description = re.search("__description__ *= *'(.*)'", data).group(1)
    url = re.search("__url__ *= *'(.*)'", data).group(1)

with open(os.path.join(ROOT, 'requirements.txt')) as f:
    requires = [x.strip() for x in f if x.strip()]

with open(os.path.join(ROOT, 'test-requirements.txt')) as f:
    test_requires = [x.strip() for x in f if x.strip()]

datadir = os.path.join('share', 'burpui', 'etc')
contrib = os.path.join('share', 'burpui', 'contrib')

setup(
    name=name,
    version=open(os.path.join(ROOT, 'burpui', 'VERSION')).read().rstrip(),
    description=description,
    long_description=readme(),
    license=open(os.path.join(ROOT, 'LICENSE')).read(),
    author=author,
    author_email=author_email,
    url=url,
    keywords='burp web ui',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'static': 'burpui/static/*',
        'templates': 'burpui/templates/*',
        'VERSION': 'burpui/VERSION',
    },
    entry_points={
        'console_scripts': [
            'burp-ui=burpui.__main__:server',
            'bui-agent=burpui.__main__:agent',
        ],
    },
    data_files=[
        (datadir, [os.path.join(datadir, 'burpui.sample.cfg')]),
        (datadir, [os.path.join(datadir, 'buiagent.sample.cfg')]),
        (os.path.join(contrib, 'centos'), ['contrib/centos/init.sh']),
        (os.path.join(contrib, 'debian'), ['contrib/debian/init.sh']),
        (os.path.join(contrib, 'gunicorn.d'), ['contrib/gunicorn.d/burp-ui']),
    ],
    install_requires=requires,
    extras_require={
        'ldap_authentication': ['ldap3'],
        'burp2': ['ujson'],
        'test': test_requires,
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
        'Topic :: System :: Monitoring',
    ],
    cmdclass={
        'build_static': BuildStatic,
        'develop': DevelopWithBuildStatic,
        'sdist': SdistWithBuildStatic,
        'install': CustomInstall,
        'bdist_egg': BdistWithBuildStatic,
        'egg_info': EggWithBuildStatic,
        'test': PyTest,
    }
)
