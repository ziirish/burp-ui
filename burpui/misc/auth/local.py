# -*- coding: utf8 -*-
import os
import pwd
import sys

from flask_login import AnonymousUserMixin
from .interface import BUIhandler, BUIuser, BUIloader
from ...utils import __


class LocalLoader(BUIloader):
    """The :class:`burpui.misc.auth.local.LocalLoader` class loads the *Local*
    users.
    """
    section = name = 'LOCAL'

    def __init__(self, app=None, handler=None):
        """:func:`burpui.misc.auth.Local.localLoader.__init__` loads users from
        the configuration file.

        :param app: Instance of the app we are running in
        :type app: :class:`burpui.server.BUIServer`
        """
        self.app = app
        self.users = None
        handler.name = self.name
        limit = 1000
        conf = self.app.conf
        if self.section in conf.options:
            # Maybe the handler argument is None, maybe the 'priority'
            # option is missing. We don't care.
            try:
                handler.priority = conf.safe_get(
                    'priority',
                    'integer',
                    section=self.section
                ) or handler.priority
            except:
                pass
            users = conf.safe_get(
                'users',
                cast='force_list',
                section=self.section
            )
            limit = conf.safe_get(
                'limit',
                cast='integer',
                section=self.section,
                defaults={self.section: {'limit': limit}}
            )
            if users != [None]:
                self.users = users

        if self.users is None:
            self.users = []
            for user in pwd.getpwall():
                if user[2] >= limit:
                    self.users.append(user[0])

        self.logger.debug('Local users: ' + str(self.users))

    def fetch(self, uid=None):
        """:func:`burpui.misc.auth.local.LocalLoader.fetch` searches for a user
        in the configuration.

        :param uid: User to search for
        :type uid: str

        :returns: The given UID if the user exists or None
        """
        if self.users is None or uid in self.users:
            return uid

        return None

    def check(self, uid=None, passwd=None):
        """:func:`burpui.misc.auth.local.LocalLoader.check` verifies if the
        given password matches the given user settings.

        :param uid: User to authenticate
        :type uid: str

        :param passwd: Password
        :type passwd: str

        :returns: True if there is a match, otherwise False
        """
        if self.users is None or uid in self.users:
            return authenticate(uid, passwd)

        return False


class UserHandler(BUIhandler):
    __doc__ = __('Authenticate users against local PAM database.')
    priority = 0

    """See :class:`burpui.misc.auth.interface.BUIhandler`"""
    def __init__(self, app=None, auth=None):
        """See :func:`burpui.misc.auth.interface.BUIhandler.__init__`"""
        self.local = LocalLoader(app, self)
        self.users = {}

    def user(self, name=None):
        """See :func:`burpui.misc.auth.interface.BUIhandler.user`"""
        if name not in self.users:
            self.users[name] = LocalUser(self.local, name)
        ret = self.users[name]
        if not ret.active:
            return AnonymousUserMixin()
        return ret

    @property
    def loader(self):
        return self.local


class LocalUser(BUIuser):
    """See :class:`burpui.misc.auth.interface.BUIuser`"""
    def __init__(self, local=None, name=None):
        self.active = False
        self.authenticated = False
        self.local = local
        self.name = name
        self.id = None
        self.backend = self.local.name

        res = self.local.fetch(self.name)

        if res:
            self.id = res
            self.active = True

    def login(self, passwd=None):
        """See :func:`burpui.misc.auth.interface.BUIuser.login`"""
        self.authenticated = self.local.check(self.name, passwd)
        return self.authenticated

    @property
    def is_active(self):  # pragma: no cover
        return self.active

    @property
    def is_authenticated(self):  # pragma: no cover
        return self.authenticated

    def get_id(self):
        return self.id


# HERE IS THE PAM MODULE FROM https://atlee.ca/software/pam/
# (c) 2007 Chris AtLee <chris@atlee.ca>
# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license.php
"""
PAM module for python

Provides an authenticate function that will allow the caller to authenticate
a user against the Pluggable Authentication Modules (PAM) on the system.

Implemented using ctypes, so no compilation is necessary.
"""
from ctypes import CDLL, POINTER, Structure, CFUNCTYPE, cast, pointer, sizeof  # noqa
from ctypes import c_void_p, c_uint, c_char_p, c_char, c_int  # noqa
from ctypes.util import find_library  # noqa


def load_library(nickname, search_names=None):
    '''Load a library based on the result of find_library(nickname),
    or hardcoded names found in `search_names`.'''

    library = None
    if search_names is None:
        search_names = []

    # We try to guess the library name using `find_library`.
    # If we found a name, we add it a the first to be tried for loading.
    guess_path = find_library(nickname)
    if guess_path is not None:
        search_names.insert(0, guess_path)

    # Try to load each name, and stop when a name was successfuly loaded.
    for name in search_names:
        try:
            library = CDLL(name)
        except OSError:
            library = None

        if library is not None:
            return library

    if library is None:
        raise AssertionError("Failed to load '%s' library." % (nickname))


def load_library_from_aix_archive(path, member_name='shr.o'):
    """
    Extract the shared object from the archive and load it as a normal
    library.
    """
    import atexit
    import tempfile

    import arpy

    def remove_file_at_exit(path):
        # Reimport os as it might be removed at exit.
        import os
        os.remove(path)

    archive = arpy.AIXBigArchive(path)
    archive.read_all_headers()
    member = archive.archived_files[member_name]
    temp_file = None
    try:
        temp_fd, path = tempfile.mkstemp()
        temp_file = os.fdopen(temp_fd, 'wb')
        atexit.register(remove_file_at_exit, path)
        temp_file.write(member.read())
    finally:
        if temp_file:
            temp_file.close()
    return CDLL(path)


if sys.platform.startswith('aix'):
    LIBPAM = load_library_from_aix_archive('/lib/libpam.a')
    LIBC = load_library_from_aix_archive('/lib/libc.a')
else:
    LIBPAM = load_library('pam', ['libpam.so', 'libpam.so.0', 'libpam.so.1'])
    LIBC = load_library('c', ['libc.so', 'libc.so.6', 'libc.so.5'])

CALLOC = LIBC.calloc
CALLOC.restype = c_void_p
CALLOC.argtypes = [c_uint, c_uint]

STRDUP = LIBC.strdup
STRDUP.argstypes = [c_char_p]
STRDUP.restype = POINTER(c_char)  # NOT c_char_p !!!!

# Various constants
PAM_PROMPT_ECHO_OFF = 1
PAM_PROMPT_ECHO_ON = 2
PAM_ERROR_MSG = 3
PAM_TEXT_INFO = 4


class PamHandle(Structure):
    """wrapper class for pam_handle_t"""
    _fields_ = [
        ("handle", c_void_p)
    ]

    def __init__(self):
        Structure.__init__(self)
        self.handle = 0


class PamMessage(Structure):
    """wrapper class for pam_message structure"""
    _fields_ = [
        ("msg_style", c_int),
        ("msg", POINTER(c_char)),
    ]

    def __repr__(self):
        return "<PamMessage %i '%s'>" % (self.msg_style, self.msg)


class PamResponse(Structure):
    """wrapper class for pam_response structure"""
    _fields_ = [
        ("resp", POINTER(c_char)),
        ("resp_retcode", c_int),
    ]

    def __repr__(self):
        return "<PamResponse %i '%s'>" % (self.resp_retcode, self.resp)


CONV_FUNC = CFUNCTYPE(c_int,
                      c_int, POINTER(POINTER(PamMessage)),
                      POINTER(POINTER(PamResponse)), c_void_p)


class PamConv(Structure):
    """wrapper class for pam_conv structure"""
    _fields_ = [
        ("conv", CONV_FUNC),
        ("appdata_ptr", c_void_p)
    ]


PAM_START = LIBPAM.pam_start
PAM_START.restype = c_int
PAM_START.argtypes = [c_char_p, c_char_p, POINTER(PamConv),
                      POINTER(PamHandle)]

PAM_END = LIBPAM.pam_end
PAM_END.restpe = c_int
PAM_END.argtypes = [PamHandle, c_int]

PAM_AUTHENTICATE = LIBPAM.pam_authenticate
PAM_AUTHENTICATE.restype = c_int
PAM_AUTHENTICATE.argtypes = [PamHandle, c_int]


def authenticate(username, password, service='login'):
    """Returns True if the given username and password authenticate for the
    given service.  Returns False otherwise

    ``username``: the username to authenticate

    ``password``: the password in plain text

    ``service``: the PAM service to authenticate against.
                 Defaults to 'login'"""
    @CONV_FUNC
    def my_conv(n_messages, messages, p_response, app_data):
        """Simple conversation function that responds to any
        prompt where the echo is off with the supplied password"""
        # Create an array of n_messages response objects
        addr = CALLOC(n_messages, sizeof(PamResponse))
        p_response[0] = cast(addr, POINTER(PamResponse))
        for i in range(n_messages):
            if messages[i].contents.msg_style == PAM_PROMPT_ECHO_OFF:
                pw_copy = STRDUP(str(password))
                p_response.contents[i].resp = cast(pw_copy, POINTER(c_char))
                p_response.contents[i].resp_retcode = 0
        return 0

    handle = PamHandle()
    conv = PamConv(my_conv, 0)
    retval = PAM_START(service, username, pointer(conv), pointer(handle))

    if retval != 0:
        # TODO: This is not an authentication error, something
        # has gone wrong starting up PAM
        PAM_END(handle, retval)
        return False

    retval = PAM_AUTHENTICATE(handle, 0)
    e = PAM_END(handle, retval)
    return retval == 0 and e == 0
