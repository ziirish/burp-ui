Introduction
============

`Burp-UI`_ is a web-based interface for `Burp`_. It's purpose is to give you a
*nice* way to monitor your backups with some dashboards, but you will also have
the ability to download files from backups and to configure your burp-server.

The project also provides a full documented `API <api.html>`_ so that you can
develop any front-end you like on top of it. The core will take care of the
communication with the burp server(s) for you.


Known Issues
------------

Because it's an Open Source project, people are free (and encouraged) to open
issues in the `bug-tracker <https://git.ziirish.me/ziirish/burp-ui/issues>`_.
You will find there the current opened issues.


There are also a few issues unrelated to the code itself:

1. SSL issue

My new SSL certificate seem to be unknown on older systems like debian wheezy.
Thus, you may have some SSL failure while trying to clone my repository.
In order to fix this error, you can run the following command as root that will
add my certificate in your trust list:

::

   echo -n | \
   openssl s_client -showcerts -connect git.ziirish.me:443 \
   -servername git.ziirish.me 2>/dev/null | \
   sed -ne '/-BEGIN CERTIFICATE-/,/-END CERTIFICATE-/p' >>/etc/ssl/certs/ca-certificates.crt


2. SSH issue

People that would like to clone the repository over SSH will face an
authentication failure even if they added a valid SSH key in their user
settings.
The reason is I only have *one* public IP address so I must use port
redirections to have multiple SSH instances running.
To fix the issue, you should configure your SSH client by adding the following
lines in your ``~/.ssh/config`` file:

::

   Host git.ziirish.me
      Port 2222


.. _Burp: http://burp.grke.org/
.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
