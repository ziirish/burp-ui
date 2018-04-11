FROM debian:jessie

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y supervisor logrotate locales wget curl uthash-dev g++ make libssl-dev librsync-dev git cron \
 && update-locale LANG=C.UTF-8 LC_MESSAGES=POSIX \
 && locale-gen en_US.UTF-8 \
 && dpkg-reconfigure -f noninteractive locales \
 && echo "Europe/Paris" >/etc/timezone \
 && dpkg-reconfigure -f noninteractive tzdata \
 && rm -rf /var/lib/apt/lists/*

ADD assets/setup/ /app/setup/
ADD assets/config/ /app/setup/config/

ADD assets/init /app/init
RUN chmod 755 /app/init

RUN chmod 755 /app/setup/install
RUN /app/setup/install

VOLUME ["/srv/demo/files:/home"]

ENTRYPOINT ["/app/init"]
CMD ["app:start"]
