Docker images
=============

In this folder you will find different `docker`_ images that will allow you to
easily set-up `Burp-UI`_.

It is organized like this:

- `demo/ <demo/>`_ contains the images used to build the demo.
- `docker-alpine/ <docker-alpine/>`_ contains a small but complete image based
  on `alpine`_ and python 3.6.

Usage
-----

A Dockerfile is provided in order to help you build the release image.

Here is how to build it:

::

    cd ..
    # alpine-based docker image:
    docker build -t $USER/burp-ui:alpine -f docker/Dockerfile .


Alternatively, images are built by the CI and you can freely use them thanks to
the provided `docker-compose`_ config:

::

    docker-compose pull
    docker-compose up -d

.. _docker: https://www.docker.com/
.. _docker-compose: https://docs.docker.com/compose/
.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
.. _alpine: https://alpinelinux.org/
