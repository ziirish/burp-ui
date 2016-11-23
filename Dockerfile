FROM debian:jessie
MAINTAINER hi+burpui@ziirish.me

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y supervisor logrotate locales wget python2.7-dev git gunicorn python-pip cron libffi-dev netcat \
 && update-locale LANG=C.UTF-8 LC_MESSAGES=POSIX \
 && locale-gen en_US.UTF-8 \
 && dpkg-reconfigure -f noninteractive locales \
 && echo "Europe/Paris" >/etc/timezone \
 && dpkg-reconfigure -f noninteractive tzdata \
 && rm -rf /var/lib/apt/lists/*

ADD . /burp-ui

ADD docker/docker-release/assets/setup/ /app/setup/
ADD docker/docker-release/assets/config/ /app/setup/config/
ADD docker/docker-release/assets/init /app/init

RUN chmod 755 /app/init
RUN chmod 755 /app/setup/install
RUN /app/setup/install

EXPOSE 5000/tcp

VOLUME ["/var/spool/burp"]
VOLUME ["/etc/burp"]

ENTRYPOINT ["/app/init"]
CMD ["app:start"]
