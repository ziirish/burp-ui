# -*- coding: utf8 -*-
"""
Burp-UI is a web-ui for burp backup written in python with Flask and
jQuery/Bootstrap

.. module:: burpui.cli
    :platform: Unix
    :synopsis: Burp-UI CLI module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>
"""
import os
import sys
import time

import click

if os.getenv("BUI_MODE") in ["server", "ws"] or "websocket" in sys.argv:
    try:
        from gevent import monkey

        monkey.patch_socket()
    except ImportError:
        pass

from .app import create_app  # noqa
from .exceptions import BUIserverException  # noqa

try:
    from flask_socketio import SocketIO  # noqa

    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False

ROOT = os.path.dirname(os.path.realpath(__file__))
DEBUG = os.getenv("BUI_DEBUG") or os.getenv("FLASK_DEBUG") or False
DEBUG = DEBUG and DEBUG.lower() not in ["false", "no", "0"]

VERBOSE = os.getenv("BUI_VERBOSE") or 0
if VERBOSE:
    try:
        VERBOSE = int(VERBOSE)
    except ValueError:
        VERBOSE = 0

# UNITTEST is used to skip the burp-2 requirements for modes != server
UNITTEST = os.getenv("BUI_MODE") not in ["server", "manage", "celery", "legacy", "ws"]
CLI = os.getenv("BUI_MODE") not in ["server", "legacy"]

app = create_app(
    conf=os.environ.get("BUI_CONFIG"),
    verbose=VERBOSE,
    logfile=os.environ.get("BUI_LOGFILE"),
    debug=DEBUG,
    gunicorn=False,
    unittest=UNITTEST,
    cli=CLI,
    websocket_server=(os.getenv("BUI_MODE") == "ws" or "websocket" in sys.argv),
)

try:
    from flask_migrate import Migrate

    from .ext.sql import db
    from .extensions import create_db

    # This may have been reseted by create_app
    if isinstance(app.database, bool):
        app.config["WITH_SQL"] = app.database
    else:
        app.config["WITH_SQL"] = app.database and app.database.lower() != "none"

    if app.config["WITH_SQL"]:
        create_db(app, True)

        mig_dir = os.getenv("BUI_MIGRATIONS")
        if mig_dir:
            migrate = Migrate(app, db, mig_dir)
        else:
            migrate = Migrate(app, db)
except ImportError:
    pass

# Utilities functions


def _die(error, appli=None):
    appli = " '{}'".format(appli) if appli else ""
    err(
        "Unable to initialize the application{}: {}".format(appli, error),
    )
    sys.exit(2)


def _log(message, *args, color=None, err=False):
    msg = message % args if args else message
    if color is not None:
        msg = click.style(msg, fg=color)
    click.echo(msg, err=err)


def log(message="", *args):
    _log(message, *args)


def ok(message="", *args):
    _log(message, *args, color="green")


def info(message="", *args):
    _log(message, *args, color="blue")


def warn(message="", *args):
    _log(message, *args, color="yellow")


def err(message="", *args, err=True):
    _log(message, *args, color="red", err=err)


@app.cli.command()
def legacy():
    """Legacy server for backward compatibility."""
    warn(
        "If you want to pass options, you should run 'python -m burpui "
        "-m legacy [...]' instead",
    )
    app.manual_run()


@app.cli.command()
@click.option(
    "-b",
    "--bind",
    default="127.0.0.1",
    help="Which address to bind to for the websocket server",
)
@click.option(
    "-p",
    "--port",
    default=5001,
    help="Which port to listen on for the websocket server",
)
@click.option(
    "-d",
    "--debug",
    default=False,
    is_flag=True,
    help="Whether to start the websocket server in debug mode",
)
def websocket(bind, port, debug):
    """Start a new websocket server."""
    try:
        from .ext.ws import socketio
    except ImportError:
        _die(
            "Missing requirement, did you ran 'pip install" ' "burp-ui[websocket]"\'?',
            "websocket",
        )
    socketio.run(app, host=bind, port=port, debug=debug)


@app.cli.command()
@click.option(
    "-b", "--backend", default="BASIC", help="User Backend (default is BASIC)."
)
@click.option("-p", "--password", help="Password to assign to user.", default=None)
@click.option(
    "-a",
    "--ask",
    default=False,
    is_flag=True,
    help="If no password is provided and this flag is enabled, "
    "you'll be prompted for one, else a random one will be "
    "generated.",
)
@click.option(
    "-v", "--verbose", default=False, is_flag=True, help="Add extra debug messages."
)
@click.argument("name")
def create_user(backend, password, ask, verbose, name):
    """Create a new user."""
    try:
        msg = app.load_modules()
    except Exception as e:
        msg = str(e)

    if not backend.endswith(":AUTH"):
        backend = f"{backend}:AUTH"
    backend = backend.upper()

    if msg:
        _die(msg, "create_user")

    info("[*] Adding '{}' user...".format(name))
    try:
        handler = getattr(app, "uhandler")
    except AttributeError:
        handler = None

    if not handler or len(handler.backends) == 0 or backend not in handler.backends:
        err("[!] No authentication backend found")
        sys.exit(1)

    back = handler.backends[backend]

    if back.add_user is False:
        err("[!] The '{}' backend does not support user creation".format(backend))
        sys.exit(2)

    if not password:
        if ask:
            import getpass

            password = getpass.getpass()
            confirm = getpass.getpass("Confirm: ")
            if password != confirm:
                err("[!] Passwords mismatch")
                sys.exit(3)
        else:
            import random

            alphabet = (
                "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLM" "NOPQRSTUVWXYZ"
            )
            pw_length = 8
            mypw = ""

            for i in range(pw_length):
                next_index = random.randrange(len(alphabet))
                mypw += alphabet[next_index]
            password = mypw
            info("[+] Generated password: {}".format(password))

    success, message, _ = back.add_user(name, password)
    _log(
        "[+] Success: {}{}".format(
            success, " -> {}".format(message) if verbose and message else ""
        ),
        color="green" if success else "red",
    )


@app.cli.command()
@click.option("-p", "--password", help="Password to assign to user.", default=None)
@click.option(
    "-u",
    "--username",
    help="Provide the username to get the full " "configuration line.",
    default=None,
)
@click.option(
    "-b",
    "--batch",
    default=False,
    is_flag=True,
    help="Don't be extra verbose so that you can use the output "
    "directly in your scripts. Requires both -u and -p.",
)
def hash_password(password, username, batch):
    """Hash a given password to fill the configuration file."""
    from werkzeug.security import generate_password_hash

    if batch and (not username or not password):
        err(
            "You need to provide both a username and a password using the "
            "-u and -p flags!",
        )
        sys.exit(1)

    askpass = False
    if not password:
        askpass = True
        import getpass

        password = getpass.getpass()

    hashed = generate_password_hash(password)
    if not batch:
        log("'{}' hashed into: {}".format(password if not askpass else "*" * 8, hashed))
    if username:
        if not batch:
            info("#8<{}".format("-" * 77))
        log("{} = {}".format(username, hashed))
        if not batch:
            info("#8<{}".format("-" * 77))


@app.cli.command()
@click.argument("language")
def init_translation(language):
    """Initialize a new translation for the given language."""
    try:
        import babel  # noqa
    except ImportError:
        warn("Missing i18n requirements, giving up")
        return
    os.chdir(os.path.join(ROOT, ".."))
    os.system(
        "pybabel extract -F babel.cfg -k __ -k lazy_gettext -o messages.pot burpui"
    )
    os.system(
        "pybabel init -i messages.pot -d burpui/translations -l {}".format(language)
    )
    os.unlink("messages.pot")


@app.cli.command()
def update_translation():
    """Update translation files."""
    try:
        import babel  # noqa
    except ImportError:
        warn("Missing i18n requirements, giving up")
        return
    os.chdir(os.path.join(ROOT, ".."))
    os.system(
        "pybabel extract -F babel.cfg -k __ -k lazy_gettext -o messages.pot burpui"
    )
    os.system("pybabel update -i messages.pot -d burpui/translations")
    os.unlink("messages.pot")


@app.cli.command()
def compile_translation():
    """Compile translations."""
    try:
        import babel  # noqa
    except ImportError:
        warn("Missing i18n requirements, giving up")
        return
    os.chdir(os.path.join(ROOT, ".."))
    os.system("pybabel compile -f -d burpui/translations")


@app.cli.command()
@click.option(
    "-b",
    "--burp-conf-cli",
    "bconfcli",
    default=None,
    help="Burp client configuration file",
)
@click.option(
    "-s",
    "--burp-conf-serv",
    "bconfsrv",
    default=None,
    help="Burp server configuration file",
)
@click.option(
    "-c",
    "--client",
    default="bui",
    help="Name of the burp client that will be used by Burp-UI " '(defaults to "bui")',
)
@click.option(
    "-l",
    "--listen",
    default="0.0.0.0:5971",
    help="Setup a custom listen port for the Burp-UI restorations",
)
@click.option(
    "-h",
    "--host",
    default="::1",
    help='Address of the status server (defaults to "::1")',
)
@click.option("-r", "--redis", default=None, help="Redis URL to connect to")
@click.option(
    "-d",
    "--database",
    default=None,
    help="Database to connect to for persistent storage",
)
@click.option("-p", "--plugins", default=None, help="Plugins location")
@click.option("-m", "--monitor", default=None, help="bui-monitor configuration file")
@click.option(
    "-i", "--monitor-listen", "mbind", default=None, help="bui-monitor bind address"
)
@click.option(
    "-C",
    "--concurrency",
    default=None,
    type=click.INT,
    help="Number of concurrent requests addressed to the monitor",
)
@click.option(
    "-P",
    "--pool-size",
    "pool",
    default=None,
    type=click.INT,
    help="Number of burp-client processes to spawn in the monitor",
)
@click.option(
    "-B",
    "--backend",
    default=None,
    help="Switch to another backend",
    type=click.Choice(["burp2", "parallel"]),
)
@click.option(
    "-a",
    "--assume-version",
    "assume",
    default=None,
    help="If we cannot determine server version use this one",
)
@click.option(
    "-n",
    "--dry",
    is_flag=True,
    help="Dry mode. Do not edit the files but display changes",
)
def setup_burp(
    bconfcli,
    bconfsrv,
    client,
    listen,
    host,
    redis,
    database,
    plugins,
    monitor,
    mbind,
    concurrency,
    pool,
    backend,
    assume,
    dry,
):
    """Setup burp client for burp-ui."""
    if app.config["BACKEND"] not in ["burp2", "parallel"] and not backend:
        err("Sorry, you can only setup the 'burp2' and the 'parallel' backends")
        sys.exit(1)

    if not app.config["STANDALONE"]:
        err("Sorry, only the standalone mode is supported")
        sys.exit(1)

    if concurrency:
        from multiprocessing import cpu_count

        if concurrency > cpu_count():
            warn(
                "Warning: setting a concurrency level higher than the available CPU"
                " count might cause you some troubles"
            )

    if pool and concurrency:
        if concurrency > pool:
            warn(
                "Warning: setting a concurrency level higher than the available"
                " processes in the monitor is not recommended"
            )

    is_parallel = app.config["BACKEND"] == "parallel" or (
        backend and backend == "parallel"
    )

    # enforce burp2 backend for the configuration
    app.config["BACKEND"] = "burp2"

    try:
        msg = app.load_modules()
    except Exception as e:
        msg = str(e)

    if msg:
        _die(msg, "setup-burp")

    import difflib
    import tempfile

    from .app import get_redis_server
    from .config import BUIConfig
    from .misc.backend.utils.constant import BURP_BIND_MULTIPLE, BURP_LISTEN_OPTION
    from .misc.parser.utils import Config

    if monitor:
        monconf = BUIConfig(monitor)
        monconf_orig = []
        mon_orig = mon_source = monitor

        if dry:
            try:
                with open(monitor) as fil:
                    monconf_orig = fil.readlines()
            except:
                pass

            (_, temp) = tempfile.mkstemp()
            monconf.options.filename = temp

    parser = app.client.get_parser()
    server_version = app.client.get_server_version() or assume
    orig = source = None
    conf_orig = []
    if dry:
        try:
            with open(app.conf.options.filename) as fil:
                conf_orig = fil.readlines()
        except:
            pass

        orig = source = app.conf.options.filename
        (_, temp) = tempfile.mkstemp()
        app.conf.options.filename = temp

    # handle migration of old config files
    if app.conf.section_exists("Burp2"):
        if app.conf.rename_section("Burp2", "Burp", source):
            info("Renaming old [Burp2] section")
            app.conf._refresh(True)

    refresh = False
    if not app.conf.lookup_section("Burp", source):
        refresh = True
    if not app.conf.lookup_section("Global", source):
        refresh = True
    if (database or redis) and not app.conf.lookup_section("Production", source):
        refresh = True
    if concurrency and not app.conf.lookup_section("Parallel", source):
        refresh = True

    if refresh:
        app.conf._refresh(True)

    if monitor and not monconf.lookup_section("Global", mon_source):
        monconf._refresh(True)

    def _edit_conf(key, val, attr, section="Burp", obj=app.client, conf=app.conf):
        if val and (
            (key not in conf.options[section])
            or (key in conf.options[section] and val != conf.options[section][key])
        ):
            adding = key not in conf.options[section]
            conf.options[section][key] = val
            conf.options.write()
            if obj:
                setattr(obj, attr, val)
            if adding:
                msg = f'Adding new option "{key}={val}" to section [{section}] in {conf.conffile}'
            else:
                msg = f'Updating option "{key}={val}" in section [{section}] in {conf.conffile}'
            info(msg)
            return True
        return False

    def _color_diff(line):
        if line.startswith("+"):
            return click.style(line, fg="green")
        elif line.startswith("-"):
            return click.style(line, fg="red")
        elif line.startswith("^"):
            return click.style(line, fg="blue")
        return line

    refresh = False
    refresh |= _edit_conf("bconfcli", bconfcli, "burpconfcli")
    refresh |= _edit_conf("bconfsrv", bconfsrv, "burpconfsrv")
    refresh |= _edit_conf("plugins", plugins, "plugins", "Global", app)
    if backend:
        refresh |= _edit_conf("backend", backend, None, "Global", None)
    if is_parallel and concurrency:
        refresh |= _edit_conf("concurrency", concurrency, None, "Parallel", None)
    if mbind:
        refresh |= _edit_conf("host", mbind, None, "Parallel", None)

    if refresh:
        app.conf._refresh(True)

    refresh = False
    if monitor and pool:
        refresh |= _edit_conf("pool", pool, None, "Global", None, monconf)
    if monitor and mbind:
        refresh |= _edit_conf("bind", mbind, None, "Global", None, monconf)
    if monitor:
        refresh |= _edit_conf("bconfcli", bconfcli, None, "Burp", None, monconf)

    if refresh:
        monconf._refresh(True)

    if monitor and app.config["BACKEND"] == "parallel":
        mon_password = monconf.options["Global"].get("password")
        back_password = app.conf.options["Parallel"].get("password")

        if mon_password != back_password:
            click.echo(
                click.style(
                    "Backend password does not match monitor password", fg="yellow"
                )
            )

    if redis:
        try:
            # detect missing modules
            import socket

            import celery  # noqa
            import redis as redis_client  # noqa

            if (
                "redis" not in app.conf.options["Production"]
                or "redis" in app.conf.options["Production"]
                and app.conf.options["Production"]["redis"] != redis
            ) and app.redis != redis:
                app.conf.options["Production"]["redis"] = redis
                app.redis = redis

            rhost, rport, _ = get_redis_server(app)
            ret = -1
            for _ in range(10):
                if ret == 0:
                    break

                for res in socket.getaddrinfo(
                    rhost, rport, socket.AF_UNSPEC, socket.SOCK_STREAM
                ):
                    if ret == 0:
                        break
                    af, socktype, proto, _, sa = res
                    try:
                        s = socket.socket(af, socktype, proto)
                    except socket.error:
                        continue
                    try:
                        ret = s.connect_ex(sa)
                    except:
                        continue

                time.sleep(1)

            if ret == 0:
                app.conf.options["Production"]["celery"] = "true"

                app.conf.options["Production"]["storage"] = "redis"

                app.conf.options["Production"]["cache"] = "redis"
            else:
                warn("Unable to contact the redis server, disabling it")
                app.conf.options["Production"]["storage"] = "default"
                app.conf.options["Production"]["cache"] = "default"
                if app.use_celery:
                    app.conf.options["Production"]["celery"] = "false"

            app.conf.options.write()
            app.conf._refresh(True)
        except ImportError:
            warn(
                "Unable to activate redis & celery. Did you ran the "
                "'pip install burp-ui[celery]' and "
                "'pip install burp-ui[gunicorn-extra]' commands first?"
            )

    if database:
        try:
            from .ext.sql import db  # noqa

            if (
                "database" not in app.conf.options["Production"]
                or "database" in app.conf.options["Production"]
                and app.conf.options["Production"]["database"] != database
            ) and app.database != database:
                app.conf.options["Production"]["database"] = database
                app.conf.options.write()
                app.conf._refresh(True)
        except ImportError:
            warn(
                "It looks like some dependencies are missing. Did you ran "
                "the 'pip install \"burp-ui[sql]\"' command first?"
            )

    if dry:
        temp = app.conf.options.filename
        app.conf.options.filename = orig
        after = []
        try:
            if not os.path.exists(temp) or os.path.getsize(temp) == 0:
                after = conf_orig
            else:
                with open(temp) as fil:
                    after = fil.readlines()
                os.unlink(temp)
        except:
            pass
        diff = difflib.unified_diff(
            conf_orig, after, fromfile=orig, tofile="{}.new".format(orig)
        )
        out = ""
        for line in diff:
            out += _color_diff(line)
        if out:
            click.echo_via_pager(out)

    if dry and monitor:
        temp = monconf.options.filename
        monconf.options.filename = mon_orig
        after = []
        try:
            if not os.path.exists(temp) or os.path.getsize(temp) == 0:
                after = monconf_orig
            else:
                with open(temp) as fil:
                    after = fil.readlines()
                os.unlink(temp)
        except:
            pass
        diff = difflib.unified_diff(
            monconf_orig, after, fromfile=mon_orig, tofile="{}.new".format(mon_orig)
        )
        out = ""
        for line in diff:
            out += _color_diff(line)
        if out:
            click.echo_via_pager(out)

    bconfcli = (
        bconfcli
        or app.conf.options["Burp"].get("bconfcli")
        or getattr(app.client, "burpconfcli")
    )
    bconfsrv = (
        bconfsrv
        or app.conf.options["Burp"].get("bconfsrv")
        or getattr(app.client, "burpconfsrv")
    )
    dest_bconfcli = bconfcli

    is_burp_2_2_10_plus = False
    listen_opt = "status_address"
    if server_version and server_version >= BURP_LISTEN_OPTION:
        is_burp_2_2_10_plus = True
        listen_opt = "listen_status"

    _, restore_port = listen.split(":")

    if not os.path.exists(bconfcli):
        clitpl = f"""
mode = client
port = {restore_port}
status_port = 4972
server = ::1
password = abcdefgh
cname = {client}
protocol = 1
pidfile = /tmp/burp.client.pid
syslog = 0
stdout = 1
progress_counter = 1
network_timeout = 72000
server_can_restore = 0
cross_all_filesystems=0
ca_burp_ca = /usr/sbin/burp_ca
ca_csr_dir = /etc/burp/CA-client
ssl_cert_ca = /etc/burp/ssl_cert_ca-client-{client}.pem
ssl_cert = /etc/burp/ssl_cert-bui-client.pem
ssl_key = /etc/burp/ssl_cert-bui-client.key
ssl_key_password = password
ssl_peer_cn = burpserver
include = /home
exclude_fs = sysfs
exclude_fs = tmpfs
nobackup = .nobackup
exclude_comp=bz2
exclude_comp=gz
"""

        if dry:
            (_, dest_bconfcli) = tempfile.mkstemp()
        with open(dest_bconfcli, "w") as confcli:
            confcli.write(clitpl)

    parser = app.client.get_parser(assume)

    confcli = Config(dest_bconfcli, parser, "srv")
    confcli.set_default(dest_bconfcli)
    confcli.parse()

    if confcli.get("cname") != client:
        confcli["cname"] = client
    if confcli.get("server") != host:
        confcli["server"] = host
    c_status_port = (
        confcli.get("status_port", [4972])[0]
        if confcli.version >= BURP_BIND_MULTIPLE
        else confcli.get("status_port", 4972)
    )
    c_server_port = (
        confcli.get("port", [4971])[0]
        if confcli.version >= BURP_BIND_MULTIPLE
        else confcli.get("port", 4971)
    )
    if c_server_port != restore_port:
        confcli["port"] = [restore_port]

    if confcli.dirty:
        if dry:
            (_, dstfile) = tempfile.mkstemp()
        else:
            dstfile = bconfcli

        confcli.store(conf=bconfcli, dest=dstfile, insecure=True)
        if dry:
            before = []
            after = []
            try:
                with open(bconfcli) as fil:
                    before = fil.readlines()
            except:
                pass
            try:
                with open(dstfile) as fil:
                    after = fil.readlines()
                os.unlink(dstfile)
            except:
                pass

            if dest_bconfcli != bconfcli:
                # the file did not exist
                os.unlink(dest_bconfcli)
                before = []

            diff = difflib.unified_diff(
                before, after, fromfile=bconfcli, tofile="{}.new".format(bconfcli)
            )
            out = ""
            for line in diff:
                out += _color_diff(line)
            if out:
                click.echo_via_pager(out)

    if not os.path.exists(bconfsrv):
        err("Unable to locate burp-server configuration, aborting!")
        sys.exit(1)

    confsrv = Config(bconfsrv, parser, "srv")
    confsrv.set_default(bconfsrv)
    confsrv.parse()

    bind_index = -1

    if host not in ["::1", "127.0.0.1"]:
        bind = confsrv.get(listen_opt)
        if is_burp_2_2_10_plus:
            bind_list = list(bind)
            for idx, line in enumerate(bind_list):
                if line.endswith(":{}".format(c_status_port)):
                    bind = line.split(":")[0]
                    bind_index = idx
                    break
            else:
                warn(
                    "Unable to locate a 'listen_status' associated to your client "
                    "'status_port' ({})".format(c_status_port)
                )
        if (bind and bind not in [host, "::", "0.0.0.0"]) or not bind:
            warn(
                "It looks like your burp server is not exposing it's "
                "status port in a way that is reachable by Burp-UI!"
            )
            info(
                "You may want to set the '{0}' setting with "
                "either '{1}{3}', '::{3}' or '0.0.0.0{3}' in the {2} file "
                "in order to make Burp-UI work".format(
                    listen_opt,
                    host,
                    bconfsrv,
                    ":{}".format(c_status_port) if is_burp_2_2_10_plus else "",
                )
            )

    MAX_STATUS_CHILDREN = pool if pool is not None else 15
    if not is_burp_2_2_10_plus:
        s_port = confsrv.get("port", [4971])
        if restore_port not in s_port:
            confsrv["port"] = restore_port
    else:
        s_listen = confsrv.get("listen", [])
        if listen not in s_listen:
            confsrv["listen"] = listen
    status_port = confsrv.get("status_port", [4972])
    do_warn = False
    if "max_status_children" not in confsrv:
        info(
            "We need to set the number of 'max_status_children'. "
            "Setting it to {}.".format(MAX_STATUS_CHILDREN)
        )
        confsrv["max_status_children"] = MAX_STATUS_CHILDREN
    elif confsrv.version and confsrv.version < BURP_BIND_MULTIPLE:
        max_status_children = confsrv.get("max_status_children")
        if not max_status_children or max_status_children < MAX_STATUS_CHILDREN:
            confsrv["max_status_children"] = MAX_STATUS_CHILDREN
            do_warn = True
    else:
        max_status_children = confsrv.get("max_status_children", [])
        if not is_burp_2_2_10_plus:
            for idx, value in enumerate(status_port):
                if value == c_status_port:
                    bind_index = idx
                    break
        if bind_index >= 0 and len(max_status_children) >= bind_index:
            if max_status_children[bind_index] < MAX_STATUS_CHILDREN:
                confsrv["max_status_children"][bind_index] = MAX_STATUS_CHILDREN
                do_warn = True
        else:
            if max_status_children[-1] < MAX_STATUS_CHILDREN:
                confsrv["max_status_children"][-1] = MAX_STATUS_CHILDREN
                do_warn = True

    if do_warn:
        warn(
            "We need to raise the number of 'max_status_children' to {}.".format(
                MAX_STATUS_CHILDREN
            )
        )

    if "restore_client" not in confsrv:
        confsrv["restore_client"] = client
    else:
        restore = confsrv.getlist("restore_client")
        if client not in restore:
            confsrv["restore_client"].append(client)

    confsrv["monitor_browse_cache"] = True

    ca_client_dir = confsrv.get("ca_csr_dir")
    if ca_client_dir and not os.path.exists(ca_client_dir):
        try:
            os.makedirs(ca_client_dir)
        except IOError as exp:
            _log(
                'Unable to create "{}" dir: {}'.format(ca_client_dir, exp),
                color="yellow",
                err=True,
            )

    if confsrv.dirty:
        if dry:
            (_, dstfile) = tempfile.mkstemp()
        else:
            dstfile = bconfsrv

        confsrv.store(conf=bconfsrv, dest=dstfile, insecure=True)
        if dry:
            before = []
            after = []
            try:
                with open(bconfsrv) as fil:
                    before = fil.readlines()
            except:
                pass
            try:
                with open(dstfile) as fil:
                    after = fil.readlines()
                os.unlink(dstfile)
            except:
                pass
            diff = difflib.unified_diff(
                before, after, fromfile=bconfsrv, tofile="{}.new".format(bconfsrv)
            )
            out = ""
            for line in diff:
                out += _color_diff(line)
            if out:
                click.echo_via_pager(out)

    if confsrv.get("clientconfdir"):
        bconfagent = os.path.join(confsrv.get("clientconfdir"), client)
    else:
        warn(
            'Unable to find "clientconfdir" option, you will have to '
            "setup the agent by your own"
        )
        bconfagent = os.devnull

    if not os.path.exists(bconfagent):
        agenttpl = """
password = abcdefgh
"""

        if not dry:
            with open(bconfagent, "w") as confagent:
                confagent.write(agenttpl)
        else:
            before = []
            after = ["{}\n".format(x) for x in agenttpl.splitlines()]
            diff = difflib.unified_diff(
                before, after, fromfile="None", tofile=bconfagent
            )
            out = ""
            for line in diff:
                out += _color_diff(line)
            if out:
                click.echo_via_pager(out)

    else:
        confagent = Config(bconfagent, parser, "cli")
        confagent.set_default(bconfagent)
        confagent.parse()

        if confagent.get("password") != confcli.get("password"):
            warn(
                "It looks like the passwords in the {} and the {} files "
                "mismatch. Burp-UI will not work properly until you fix "
                "this".format(bconfcli, bconfagent)
            )


@app.cli.command()
@click.option(
    "-c",
    "--client",
    default="bui",
    help="Name of the burp client that will be used by Burp-UI " '(defaults to "bui")',
)
@click.option(
    "-h",
    "--host",
    default="::1",
    help='Address of the status server (defaults to "::1")',
)
@click.option("-t", "--tips", is_flag=True, help="Show you some tips")
def diag(client, host, tips):
    """Check Burp-UI is correctly setup."""
    if app.config["BACKEND"] not in ["burp2", "parallel"]:
        err("Sorry, you can only diag the 'burp2' and the 'parallel' backends")
        sys.exit(1)

    if not app.config["STANDALONE"]:
        err("Sorry, only the standalone mode is supported")
        sys.exit(1)

    try:
        msg = app.load_modules()
    except Exception as e:
        msg = str(e)

    if msg:
        _die(msg, "diag")

    from .app import get_redis_server
    from .misc.backend.utils.constant import BURP_LISTEN_OPTION
    from .misc.parser.utils import Config

    def _value_in_option(value, option, section="Production"):
        if section not in app.conf.options:
            return False
        if option not in app.conf.options[section]:
            return False
        return value in app.conf.options[section][option]

    if (
        "Production" in app.conf.options
        and "redis" in app.conf.options["Production"]
        and any(_value_in_option("redis", x) for x in ["storage", "session", "cache"])
    ):
        try:
            # detect missing modules
            import socket

            import celery  # noqa
            import redis as redis_client  # noqa

            rhost, rport, _ = get_redis_server(app)
            ret = -1
            for res in socket.getaddrinfo(
                rhost, rport, socket.AF_UNSPEC, socket.SOCK_STREAM
            ):
                if ret == 0:
                    break
                af, socktype, proto, _, sa = res
                try:
                    s = socket.socket(af, socktype, proto)
                except socket.error:
                    continue
                try:
                    ret = s.connect_ex(sa)
                except:
                    continue

            if ret != 0:
                warn("Unable to contact the redis server, disabling it")

        except ImportError:
            warn(
                "Unable to activate redis & celery. Did you ran the "
                "'pip install \"burp-ui[celery]\"' and "
                "'pip install \"burp-ui[gunicorn-extra]\"' commands first?"
            )

    if (
        "Production" in app.conf.options
        and "database" in app.conf.options["Production"]
        and app.conf.options["Production"]["database"] != "none"
    ):
        try:
            from .ext.sql import db  # noqa
        except ImportError:
            warn(
                "It looks like some dependencies are missing. Did you ran "
                "the 'pip install \"burp-ui[sql]\"' command first?"
            )

    section = "Burp"
    if not app.conf.section_exists(section):
        warn("Section [Burp] not found, looking for the old [Burp2] section instead.")
        section = "Burp2"
        if not app.conf.section_exists(section):
            err("No [Burp*] section found at all!", err=False)
            section = "Burp"

    bconfcli = app.conf.options.get(section, {}).get("bconfcli") or getattr(
        app.client, "burpconfcli"
    )
    bconfsrv = app.conf.options.get(section, {}).get("bconfsrv") or getattr(
        app.client, "burpconfsrv"
    )

    try:
        app.client.status()
    except Exception as e:
        if "Unable to spawn burp process" in str(e):
            try:
                app.client._spawn_burp(verbose=True)
            except Exception as e:
                msg = str(e)
        else:
            msg = str(e)

    if msg:
        err(msg, err=False)
        if "could not connect" in msg:
            warn(
                "It looks like your burp-client can not reach your "
                "burp-server. Please check both your 'server' setting in "
                "your '{}' file and 'status_address' in your '{}' "
                "file.".format(bconfcli, bconfsrv)
            )

    c_status_port = 4972
    errors = False
    if os.path.exists(bconfcli):
        try:
            parser = app.client.get_parser()

            confcli = Config(bconfcli, parser, "srv")
            confcli.set_default(bconfcli)
            confcli.parse()

            c_status_port = confcli.get("status_port", [4972])[0]

            if confcli.get("cname") != client:
                warn(
                    "The cname of your burp client does not match: "
                    "{} != {}".format(confcli.get("cname"), client)
                )
                errors = True
            if confcli.get("server") != host:
                warn(
                    "The burp server address does not match: "
                    "{} != {}".format(confcli.get("server"), host)
                )
                errors = True
        except BUIserverException as exc:
            err(str(exc))
            errors = True

    else:
        err("No client conf file found: {} does not exist".format(bconfcli))
        errors = True

    if os.path.exists(bconfsrv):
        try:
            is_burp_2_2_10_plus = False
            listen_opt = "status_address"
            server_version = app.client.get_server_version()
            if server_version and server_version >= BURP_LISTEN_OPTION:
                is_burp_2_2_10_plus = True
                listen_opt = "listen_status"

            parser = app.client.get_parser()

            confsrv = Config(bconfsrv, parser, "srv")
            confsrv.set_default(bconfsrv)
            confsrv.parse()

            bind_index = -1

            if host not in ["::1", "127.0.0.1"]:
                bind = confsrv.get(listen_opt)
                if is_burp_2_2_10_plus:
                    bind_list = list(bind)
                    for idx, line in enumerate(bind_list):
                        if line.endswith(":{}".format(c_status_port)):
                            bind = line.split(":")[0]
                            bind_index = idx
                            break
                    else:
                        warn(
                            "Unable to locate a 'listen_status' associated to your client "
                            "'status_port' ({})".format(c_status_port)
                        )
                if (bind and bind not in [host, "::", "0.0.0.0"]) or not bind:
                    warn(
                        "It looks like your burp server is not exposing it's "
                        "status port in a way that is reachable by Burp-UI!"
                    )
                    info(
                        "You may want to set the '{0}' setting with "
                        "either '{1}{3}', '::{3}' or '0.0.0.0{3}' in the {2} file "
                        "in order to make Burp-UI work".format(
                            listen_opt,
                            host,
                            bconfsrv,
                            ":{}".format(c_status_port) if is_burp_2_2_10_plus else "",
                        )
                    )
                    errors = True

            status_port = confsrv.get("status_port", [4972])
            if "max_status_children" not in confsrv:
                do_warn = True
            else:
                max_status_children = confsrv.get("max_status_children", [])
                do_warn = False
                if not is_burp_2_2_10_plus:
                    for idx, value in enumerate(status_port):
                        if value == c_status_port:
                            bind_index = idx
                            break
                if bind_index >= 0 and len(max_status_children) >= bind_index:
                    if max_status_children[bind_index] < 15:
                        do_warn = True
                else:
                    if max_status_children[-1] < 15:
                        do_warn = True
            if do_warn:
                info(
                    "'max_status_children' is to low, you need to set it to "
                    "15 or more. Please edit your {} file.".format(bconfsrv)
                )
                errors = True

            restore = []
            if "restore_client" in confsrv:
                restore = confsrv.getlist("restore_client")

            if client not in restore:
                warn(
                    "Your burp client is not listed as a 'restore_client'. "
                    "You won't be able to view other clients stats!"
                )
                errors = True

            if "monitor_browse_cache" not in confsrv or not confsrv.get(
                "monitor_browse_cache"
            ):
                warn(
                    "For performance reasons, it is recommended to enable the "
                    "'monitor_browse_cache'."
                )
                errors = True

            ca_client_dir = confsrv.get("ca_csr_dir")
            if ca_client_dir and not os.path.exists(ca_client_dir):
                try:
                    os.makedirs(ca_client_dir)
                except IOError as exp:
                    _log(
                        'Unable to create "{}" dir: {}'.format(ca_client_dir, exp),
                        color="yellow",
                        err=True,
                    )

            if confsrv.get("clientconfdir"):
                bconfagent = os.path.join(confsrv.get("clientconfdir"), client)
            else:
                warn(
                    'Unable to find "clientconfdir" option. Something is wrong '
                    "with your setup."
                )
                bconfagent = "ihopethisfiledoesnotexistbecauseitisrelatedtoburpui"

            if not os.path.exists(bconfagent) and bconfagent.startswith("/"):
                warn("Unable to find the {} file.".format(bconfagent))
                errors = True
            else:
                confagent = Config(bconfagent, parser, "cli")
                confagent.set_default(bconfagent)
                confagent.parse()

                if confagent.get("password") != confcli.get("password"):
                    warn(
                        "It looks like the passwords in the {} and the {} files "
                        "mismatch. Burp-UI will not work properly until you fix "
                        "this.".format(bconfcli, bconfagent)
                    )
        except BUIserverException as exc:
            err(str(exc))
            errors = True
    else:
        err(
            "Unable to locate burp-server configuration: {} does not "
            "exist.".format(bconfsrv)
        )
        errors = True

    if errors:
        if not tips:
            err(
                "Some errors have been found in your configuration. "
                "Please make sure you ran this command with the right flags! "
                "(see --help for details)."
            )
        else:
            info(
                "\n"
                "Well, if you are sure about your settings, you can run the "
                "following command to help you setup your Burp-UI agent. "
                "(Note, the '--dry' flag is here to show you the "
                "modifications that will be applied. Once you are OK with "
                "those, you can re-run the command without the '--dry' flag):"
            )
            log(
                '    > bui-manage setup-burp --host="{}" --client="{}" --dry'.format(
                    host, client
                )
            )
    else:
        ok(
            "Congratulations! It seems everything is alright. Burp-UI "
            "should run without any issue now.",
        )


@app.cli.command()
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Dump parts of the config (Please double check no sensitive" " data leaked)",
)
@click.option(
    "-l", "--load", is_flag=True, help="Load all configured modules for full summary"
)
def sysinfo(verbose, load):
    """Returns a couple of system informations to help debugging."""
    import platform

    from .desc import __release__, __version__

    msg = None
    if load:
        try:
            msg = app.load_modules()
        except Exception as e:
            msg = str(e)

    backend = app.config["BACKEND"]

    colors = {
        "True": "green",
        "False": "red",
    }
    embedded_ws = str(app.config["WITH_WS"])
    available_ws = str(WS_AVAILABLE)

    log(
        "Python version:      {}.{}.{}".format(
            sys.version_info[0], sys.version_info[1], sys.version_info[2]
        )
    )
    log("Burp-UI version:     {} ({})".format(__version__, __release__))
    log(
        "OS:                  {}:{} ({})".format(
            platform.system(), platform.release(), os.name
        )
    )
    log("Single mode:         {}".format(app.config["STANDALONE"]))
    log("Backend:             {}".format(backend))
    log(
        "WebSocket embedded:  {}".format(
            click.style(embedded_ws, fg=colors[embedded_ws])
        )
    )
    log(
        "WebSocket available: {}".format(
            click.style(available_ws, colors[available_ws])
        )
    )
    log("Config file:         {}".format(app.config.conffile))
    if load:
        if not app.config["STANDALONE"] and not msg:
            log("Agents:")
            for agent, obj in app.client.servers.items():
                client_version = server_version = "unknown"
                try:
                    app.client.status(agent=agent)
                    client_version = app.client.get_client_version(agent=agent)
                    server_version = app.client.get_server_version(agent=agent)
                except BUIserverException:
                    pass
                alive = obj.ping()
                if alive:
                    status = click.style("ALIVE", fg="green")
                else:
                    status = click.style("DISCONNECTED", fg="red")
                log(" - {} ({})".format(agent, status))
                log("   * client version: {}".format(client_version))
                log("   * server version: {}".format(server_version))
        elif not msg:
            server_version = "unknown"
            try:
                app.client.status()
                server_version = app.client.get_server_version()
            except BUIserverException:
                pass
            log("Burp client version: {}".format(app.client.client_version))
            log("Burp server version: {}".format(server_version))
    if verbose:
        log(">>>>> Extra verbose informations:")
        err("!!! PLEASE MAKE SURE NO SENSITIVE DATA GET EXPOSED !!!", err=False)
        sections = [
            "WebSocket",
            "Burp",
            "Production",
            "Global",
        ]
        sections.reverse()
        for section in sections:
            if section in app.config.options:
                log()
                log("    8<{}BEGIN[{}]".format("-" * (67 - len(section)), section))
                for key, val in app.config.options.get(section, {}).items():
                    log("    {} = {}".format(key, val))
                log("    8<{}END[{}]".format("-" * (69 - len(section)), section))

    if load and msg:
        _die(msg, "sysinfo")
