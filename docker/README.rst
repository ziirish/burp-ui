Docker images
=============

In this folder you will find different `docker`_ images that will allow you to
easily set-up `Burp-UI`_.

It is organized like this:

- `demo/ <demo/>`_ contains the images used to build the demo.
- `docker-alpine/ <docker-alpine/>`_ contains a small but complete image based
  on `alpine`_ and python 3.6.
- `docker-release/ <docker-release/>`_ contains a complete image based on
  `debian`_ and python 2.7.

Usage
-----

Two Dockerfiles are provided in order to help you build those images.

Here is how to build them:

::

    cd ..
    # build the debian-based docker image:
    docker build -t $USER/burp-ui:latest -f docker/Dockerfile .
    # if you prefer the alpine-based docker image:
    docker build -t $USER/burp-ui:alpine -f docker/Dockerfile-py3.6 .


Alternatively, images are built by the CI and you can freely use them thanks to
the provided `docker-compose`_ config:

::

    docker-compose pull
    docker-compose up -d

.. _docker: https://www.docker.com/
.. _docker-compose: https://docs.docker.com/compose/
.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
.. _alpine: https://alpinelinux.org/
.. _debian: https://www.debian.org/
