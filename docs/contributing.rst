Contributing
============

Contributions are welcome. You can help in any way you want, for instance by
opening issues on the `bug tracker
<https://git.ziirish.me/ziirish/burp-ui/issues>`__, sending patches, etc.

There is also a dedicated website. Currently it only hosts a `Discourse
<http://www.discourse.org/>`__ instance where you ca discuss with each other.
No need to create another account, the one you use in the `bug tracker
<https://git.ziirish.me/ziirish/burp-ui/issues>`__ can be imported
automatically!

Feel free to use it and post your tips and remarks.

The address is: `http://burpui.ziirish.me/ <http://burpui.ziirish.me/>`__

You can financially support the project if you find it useful or if you would
like to sponsorise a feature. Details on my `website <http://ziirish.info/>`__.


Troubleshooting
---------------

In case you encounter troubles with ``Burp-UI``, you should run it with the
``-d`` flag and paste the relevant output within your bug-report.
Please also give the version of ``burp`` AND ``Burp-UI``.
Since v0.0.6 you can use the ``-V`` or ``--version`` flag in order to get your
version number.


Known Issues
------------

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
