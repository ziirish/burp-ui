FROM debian:jessie
MAINTAINER ziirish@ziirish.info

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y supervisor logrotate locales wget curl uthash-dev g++ make libssl-dev librsync-dev python2.7-dev git python-virtualenv python-pip cron libffi-dev \
 && update-locale LANG=C.UTF-8 LC_MESSAGES=POSIX \
 && locale-gen en_US.UTF-8 \
 && dpkg-reconfigure locales \
 && rm -rf /var/lib/apt/lists/*

ADD assets/setup/ /app/setup/
ADD assets/config/ /app/setup/config/

ADD assets/init /app/init
RUN chmod 755 /app/init

RUN chmod 755 /app/setup/install
RUN /app/setup/install

EXPOSE 10000/tcp

VOLUME ["/srv/demo/spool/burp1/backup:/var/spool/burp"]
VOLUME ["/srv/demo/spool/burp1/tmp:/tmp/bui"]
VOLUME ["/srv/demo/conf/burp1/clients:/etc/burp/clientconfdir"]

ENTRYPOINT ["/app/init"]
CMD ["app:start"]
