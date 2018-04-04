#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys

from subprocess import check_output, call, STDOUT
from distutils import log
from distutils.core import Command
from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.sdist import sdist
from setuptools.command.install import install
from setuptools.command.bdist_egg import bdist_egg
from setuptools.command.egg_info import egg_info

ROOT=os.path.join(os.path.dirname(os.path.realpath(__file__)))
DEVNULL = open(os.devnull, 'wb')

# Not sure bower was a great idea...
VENDOR_TO_KEEP = [
    'burpui/static/vendor/bootswatch/slate/bootstrap.min.css',
    'burpui/static/vendor/bootswatch/fonts/glyphicons-halflings-regular.eot',
    'burpui/static/vendor/bootswatch/fonts/glyphicons-halflings-regular.svg',
    'burpui/static/vendor/bootswatch/fonts/glyphicons-halflings-regular.ttf',
    'burpui/static/vendor/bootswatch/fonts/glyphicons-halflings-regular.woff',
    'burpui/static/vendor/bootswatch/fonts/glyphicons-halflings-regular.woff2',
    'burpui/static/vendor/nvd3/build/nv.d3.min.css',
    'burpui/static/vendor/datatables.net-bs/css/dataTables.bootstrap.min.css',
    'burpui/static/vendor/datatables.net-responsive-bs/css/responsive.bootstrap.min.css',
    'burpui/static/vendor/datatables.net-select-bs/css/select.bootstrap.min.css',
    'burpui/static/vendor/datatables.net-buttons-bs/css/buttons.bootstrap.min.css',
    'burpui/static/vendor/datatables.net-fixedheader-bs/css/fixedHeader.bootstrap.min.css',
    'burpui/static/vendor/jquery.fancytree/dist/skin-bootstrap/ui.fancytree.min.css',
    'burpui/static/vendor/bootstrap-switch/dist/css/bootstrap3/bootstrap-switch.min.css',
    'burpui/static/vendor/angular-ui-select/dist/select.min.css',
    'burpui/static/vendor/jquery/dist/jquery.min.js',
    'burpui/static/vendor/jquery-ui/jquery-ui.min.js',
    'burpui/static/vendor/bootstrap/dist/js/bootstrap.min.js',
    'burpui/static/vendor/typeahead.js/dist/typeahead.jquery.min.js',
    'burpui/static/vendor/d3/d3.min.js',
    'burpui/static/vendor/nvd3/build/nv.d3.min.js',
    'burpui/static/vendor/datatables.net/js/jquery.dataTables.min.js',
    'burpui/static/vendor/datatables.net-bs/js/dataTables.bootstrap.min.js',
    'burpui/static/vendor/datatables.net-responsive/js/dataTables.responsive.min.js',
    'burpui/static/vendor/datatables.net-responsive-bs/js/responsive.bootstrap.min.js',
    'burpui/static/vendor/datatables.net-select/js/dataTables.select.min.js',
    'burpui/static/vendor/datatables.net-buttons/js/dataTables.buttons.min.js',
    'burpui/static/vendor/datatables.net-buttons-bs/js/buttons.bootstrap.min.js',
    'burpui/static/vendor/datatables.net-fixedheader/js/dataTables.fixedHeader.min.js',
    'burpui/static/vendor/jquery.floatThead/dist/jquery.floatThead.min.js',
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
    'burpui/static/vendor/angular-ui-select/dist/select.min.js',
    'burpui/static/vendor/angular-strap/dist/angular-strap.min.js',
    'burpui/static/vendor/angular-strap/dist/angular-strap.tpl.min.js',
    'burpui/static/vendor/angular-onbeforeunload/build/angular-onbeforeunload.js',
    'burpui/static/vendor/angular-datatables-0.6.2/dist/angular-datatables.min.js',
    'burpui/static/vendor/angular-highlightjs/build/angular-highlightjs.min.js',
    'burpui/static/vendor/moment/min/moment.min.js',
    'burpui/static/vendor/moment/locale/fr.js',
    'burpui/static/vendor/moment/locale/es.js',
    'burpui/static/vendor/moment/locale/it.js',
    'burpui/static/vendor/angular-ui-calendar/src/calendar.js',
    'burpui/static/vendor/fullcalendar/dist/fullcalendar.min.css',
    'burpui/static/vendor/fullcalendar/dist/fullcalendar.print.min.css',
    'burpui/static/vendor/fullcalendar/dist/fullcalendar.min.js',
    'burpui/static/vendor/fullcalendar/dist/gcal.min.js',
    'burpui/static/vendor/fullcalendar/dist/locale/fr.js',
    'burpui/static/vendor/fullcalendar/dist/locale/es.js',
    'burpui/static/vendor/fullcalendar/dist/locale/it.js',
    'burpui/static/vendor/angular-bootstrap/ui-bootstrap.min.js',
    'burpui/static/vendor/angular-bootstrap/ui-bootstrap-tpls.min.js',
    'burpui/static/vendor/components-font-awesome/css/font-awesome.min.css',
    'burpui/static/vendor/components-font-awesome/fonts/FontAwesome.otf',
    'burpui/static/vendor/components-font-awesome/fonts/fontawesome-webfont.eot',
    'burpui/static/vendor/components-font-awesome/fonts/fontawesome-webfont.svg',
    'burpui/static/vendor/components-font-awesome/fonts/fontawesome-webfont.ttf',
    'burpui/static/vendor/components-font-awesome/fonts/fontawesome-webfont.woff',
    'burpui/static/vendor/components-font-awesome/fonts/fontawesome-webfont.woff2',
    'burpui/static/vendor/socket.io-client/dist/socket.io.js',
    'burpui/static/vendor/js-cookie/src/js.cookie.js',
    'burpui/static/vendor/ace-builds/src-min-noconflict/ace.js',
    'burpui/static/vendor/ace-builds/src-min-noconflict/mode-json.js',
    'burpui/static/vendor/ace-builds/src-min-noconflict/worker-json.js',
    'burpui/static/vendor/ace-builds/src-min-noconflict/theme-ambiance.js',
]

for p in VENDOR_TO_KEEP:
    if not os.path.exists(p):
        log.info('!! missing: {}'.format(p))


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
        try:
            errno = call(['make', 'test'])
            raise SystemExit(errno)
        except OSError:
            log.error('Looks like the tools to run the tests are missing')


class BuildStatic(Command):
    user_options = []
    description = "Install bower dependencies"
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        os.chdir(ROOT)
        log.info('compiling translations')
        call('{} ./burpui -m manage compile_translation'.format(sys.executable).split(), stderr=DEVNULL)
        log.info('getting revision number')
        rev = 'stable'
        ci = os.getenv('CI')
        commit = os.getenv('CI_COMMIT_SHA')
        if not ci and os.path.exists('.git') and call("which git", shell=True, stderr=STDOUT, stdout=DEVNULL) == 0:
            try:
                branch = check_output('git rev-parse HEAD', shell=True).rstrip()
                ver = open(os.path.join('burpui', 'VERSION')).read().rstrip()
                log.info('version: {}'.format(ver))
                if branch and 'dev' in ver:
                    rev = branch
                try:
                    log.info('revision: {}'.format(rev))
                    with open('burpui/RELEASE', 'wb') as f:
                        f.write(rev)
                except:
                    log.error('Unable to create release file')
            except:
                pass
        elif ci:
            try:
                ver = open(os.path.join('burpui', 'VERSION')).read().rstrip()
                if 'dev' in ver:
                    rev = commit
                try:
                    with open('burpui/RELEASE', 'wb') as f:
                        f.write(rev)
                except:
                    pass
            except:
                pass
        else:
            log.info('using upstream revision')
        keep = VENDOR_TO_KEEP
        dirlist = []
        for dirname, subdirs, files in os.walk('burpui/static/vendor'):
            for filename in files:
                path = os.path.join(dirname, filename)
                _, ext = os.path.splitext(path)
                if os.path.isfile(path) and path not in keep and filename not in ['bower.json', 'package.json']:
                    if (rev == 'stable' and ext == '.map') or ext != '.map':
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
            if cpt > 6:
                skip = False
            if skip:
                continue
            desc += l
    return desc

sys.path.insert(0, os.path.join(ROOT))

from burpui.desc import __author__, __author_email__, __description__, \
        __url__, __title__
name = __title__
author = __author__
author_email = __author_email__
description = __description__
url = __url__

with open(os.path.join(ROOT, 'requirements.txt')) as f:
    requires = [x.strip() for x in f if x.strip()]

dev_requires = ['flake8', 'pylint']
test_requires = [
    'Flask-Testing',
    'nose',
    'coverage',
    'mock',
    'mockredispy',
    'Flask-Session',
    'Celery',
    'redis',
    'Flask-SQLAlchemy',
    'Flask-Migrate',
    'sqlalchemy_utils',
]

datadir = os.path.join('share', 'burpui')
confdir = os.path.join(datadir, 'etc')
contrib = os.path.join(datadir, 'contrib')
migrations = [(os.path.join(datadir, root), [os.path.join(root, f) for f in files if not f.endswith('.pyc')])
    for root, dirs, files in os.walk('migrations')]

setup(
    name=name,
    version=open(os.path.join(ROOT, 'burpui', 'VERSION')).read().rstrip(),
    description=description,
    long_description=readme(),
    license=open(os.path.join(ROOT, 'LICENSE')).readline().rstrip(),
    author=author,
    author_email=author_email,
    url=url,
    keywords='burp web ui backup monitoring',
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
            'bui-celery=burpui.__main__:celery',
            'bui-manage=burpui.__main__:manage',
            'bui-agent-legacy=burpui.__main__:agent',
            'burp-ui-legacy=burpui.__main__:legacy',
        ],
    },
    data_files=[
        (confdir, [os.path.join(confdir, 'burpui.sample.cfg')]),
        (os.path.join(contrib, 'centos'), ['contrib/centos/init.sh']),
        (os.path.join(contrib, 'debian'), ['contrib/debian/init.sh', 'contrib/debian/bui-celery.init']),
        (os.path.join(contrib, 'gunicorn.d'), ['contrib/gunicorn.d/burp-ui']),
        (os.path.join(contrib, 'gunicorn'), ['contrib/gunicorn/burpui_gunicorn.py']),
        (os.path.join(contrib, 'systemd'), ['contrib/systemd/bui-agent.service', 'contrib/systemd/bui-celery.service', 'contrib/systemd/bui-gunicorn.service']),
    ] + migrations,
    install_requires=requires,
    extras_require={
        'ldap_authentication': ['ldap3'],
        'extra': ['ujson'],
        'gunicorn': ['gevent', 'gunicorn'],
        'gunicorn-extra': ['redis', 'Flask-Session==0.3.1'],
        'agent': ['gevent'],
        'ci': test_requires,
        'dev': dev_requires,
        'celery': ['Celery', 'redis'],
        'sql': ['Flask-SQLAlchemy', 'Flask-Migrate>=2.1.0', 'sqlalchemy-utils'],
        'limit': ['Flask-Limiter', 'redis'],
        'websocket': ['flask-socketio', 'redis', 'gevent-websocket'],
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
        'Programming Language :: Python :: 3.6',
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
#        'test': PyTest,
    }
)
