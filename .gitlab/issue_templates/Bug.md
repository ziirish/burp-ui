Hi,

You are about to submit a bug report.

First of all, make sure you are actually facing a bug.
If you have some questions about how to setup Burp-UI, make sure you read the
[doc](https://burp-ui.readthedocs.io/en/latest/) first and especially the
[FAQ](https://burp-ui.readthedocs.io/en/latest/faq.html) which already answers a
couple of questions.

Now, if you are sure you are facing a bug, please make sure to provide the
following informations:

- Bug summary
- Burp version: `burp -v`
- Burp-UI version: `burp-ui -V -v`
- Python version: `python --version`
- List the steps to reproduce your issue
- Any log that might help understand/reproduce the problem: `burp-ui -vvvv`
- Any piece of configuration that might help understand/reproduce the problem
- Any other information that you may find useful such as screenshots, etc.

Thanks

Below is an example of a expected bug report:

----------------------------------------

Hello,

I have some trouble with Burp-UI right now. Here is a bug report:

# Bug summary

Unable to login: SQL error

# Burp

```
$ burp -v
burp-2.0.54
```

# Burp-UI

```
$ burp-ui -V -v
burp-ui: v0.4.0 (stable)
```

# Python

```
$ python --version
Python 3.6.0
```

# Steps to reproduce

1. Go to the login page
2. Try to authenticate
3. Authentication fail with a HTTP 500 Error

# logs

```
10.0.0.100 - - [11/Apr/2017 15:10:31] "POST /login?next=%2F HTTP/1.1" 500 -
Traceback (most recent call last):
  File "/usr/local/lib/python2.7/dist-packages/flask/app.py", line 1994, in __call__
    return self.wsgi_app(environ, start_response)
  File "/opt/workspace/burp-ui/burpui/utils.py", line 412, in __call__
    return self.wsgi_app(environ, start_response)
  File "/usr/local/lib/python2.7/dist-packages/flask/app.py", line 1985, in wsgi_app
    response = self.handle_exception(e)
  File "/usr/local/lib/python2.7/dist-packages/flask_restplus/api.py", line 557, in error_router
    return original_handler(e)
  File "/usr/local/lib/python2.7/dist-packages/flask/app.py", line 1540, in handle_exception
    reraise(exc_type, exc_value, tb)
  File "/usr/local/lib/python2.7/dist-packages/flask/app.py", line 1982, in wsgi_app
    response = self.full_dispatch_request()
  File "/usr/local/lib/python2.7/dist-packages/flask/app.py", line 1614, in full_dispatch_request
    rv = self.handle_user_exception(e)
  File "/usr/local/lib/python2.7/dist-packages/flask_restplus/api.py", line 557, in error_router
    return original_handler(e)
  File "/usr/local/lib/python2.7/dist-packages/flask/app.py", line 1517, in handle_user_exception
    reraise(exc_type, exc_value, tb)
  File "/usr/local/lib/python2.7/dist-packages/flask/app.py", line 1612, in full_dispatch_request
    rv = self.dispatch_request()
  File "/usr/local/lib/python2.7/dist-packages/flask/app.py", line 1598, in dispatch_request
    return self.view_functions[rule.endpoint](**req.view_args)
  File "/opt/workspace/burp-ui/burpui/routes.py", line 409, in login
    user = bui.uhandler.user(form.username.data, refresh)
  File "/opt/workspace/burp-ui/burpui/misc/auth/handler.py", line 52, in user
    session_manager.session_expired()
  File "/opt/workspace/burp-ui/burpui/sessions.py", line 39, in session_expired
    return self.session_expired_by_id(self.get_session_id())
  File "/opt/workspace/burp-ui/burpui/sessions.py", line 47, in session_expired_by_id
    store = Session.query.filter_by(uuid=id).first()
  File "/usr/local/lib/python2.7/dist-packages/sqlalchemy/orm/query.py", line 2697, in first
    ret = list(self[0:1])
  File "/usr/local/lib/python2.7/dist-packages/sqlalchemy/orm/query.py", line 2489, in __getitem__
    return list(res)
  File "/usr/local/lib/python2.7/dist-packages/sqlalchemy/orm/query.py", line 2797, in __iter__
    return self._execute_and_instances(context)
  File "/usr/local/lib/python2.7/dist-packages/sqlalchemy/orm/query.py", line 2820, in _execute_and_instances
    result = conn.execute(querycontext.statement, self._params)
  File "/usr/local/lib/python2.7/dist-packages/sqlalchemy/engine/base.py", line 945, in execute
    return meth(self, multiparams, params)
  File "/usr/local/lib/python2.7/dist-packages/sqlalchemy/sql/elements.py", line 263, in _execute_on_connection
    return connection._execute_clauseelement(self, multiparams, params)
  File "/usr/local/lib/python2.7/dist-packages/sqlalchemy/engine/base.py", line 1053, in _execute_clauseelement
    compiled_sql, distilled_params
  File "/usr/local/lib/python2.7/dist-packages/sqlalchemy/engine/base.py", line 1189, in _execute_context
    context)
  File "/usr/local/lib/python2.7/dist-packages/sqlalchemy/engine/base.py", line 1393, in _handle_dbapi_exception
    exc_info
  File "/usr/local/lib/python2.7/dist-packages/sqlalchemy/util/compat.py", line 202, in raise_from_cause
    reraise(type(exception), exception, tb=exc_tb, cause=cause)
  File "/usr/local/lib/python2.7/dist-packages/sqlalchemy/engine/base.py", line 1182, in _execute_context
    context)
  File "/usr/local/lib/python2.7/dist-packages/sqlalchemy/engine/default.py", line 469, in do_execute
    cursor.execute(statement, parameters)
OperationalError: (sqlite3.OperationalError) no such table: session [SQL: u'SELECT session.id AS session_id, session.uuid AS session_uuid, session.user AS session_user, session.ip AS session_ip, session.ua AS session_ua, session.timestamp AS session_timestamp, session.expire AS session_expire, session.permanent AS session_permanent, session.api AS session_api \nFROM session \nWHERE session.uuid = ?\n LIMIT ? OFFSET ?'] [parameters: (u'ae350427-99f4-4592-94ec-6f6a27aee59f', 1, 0)]
```

# Configuration

```
[Global]
# burp server version 1 or 2
version = 1
# Handle multiple bui-servers or not
# If set to 'false', you will need to declare at least one 'Agent' section (see
# bellow)
single = false
# authentication plugin (mandatory)
# list the misc/auth directory to see the available backends
# to disable authentication you can set "auth: none"
# you can also chain multiple backends. Example: "auth: ldap,basic"
# the order will be respected unless you manually set a higher backend priority
auth = basic, ldap
# acl plugin
# list misc/auth directory to see the available backends
# default is no ACL
acl = basic
# You can change the prefix if you are behind a reverse-proxy under a custom
# root path. For example: /burpui
prefix = none

[Production]
# storage backend (only used with gunicorn) for session and cache
# may be either 'default' or 'redis'
storage = redis
# session database to use
# may also be a backend url like: redis://localhost:6379/0
# if set to 'redis', the backend url defaults to:
# redis://<redis_host>:<redis_port>/0
# where <redis_host> is the host part, and <redis_port> is the port part of
# the below "redis" setting
session = redis
# cache database to use
# may also be a backend url like: redis://localhost:6379/0
# if set to 'redis', the backend url defaults to:
# redis://<redis_host>:<redis_port>/1
# where <redis_host> is the host part, and <redis_port> is the port part of
# the below "redis" setting
cache = redis
# redis server to connect to
redis = localhost:6379
# whether to use celery
celery = true
# database url to store some persistent data
# example: sqlite:////var/lib/burpui/store.db
database = sqlite:////tmp/burpui.db
```

Thanks
