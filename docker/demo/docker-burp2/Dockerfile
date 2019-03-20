FROM debian:buster

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y supervisor logrotate locales wget curl uthash-dev g++ make libssl-dev librsync-dev python3-dev git python3-virtualenv python3-pip cron libffi-dev autoconf automake libtool libz-dev libyajl-dev gnupg \
 && update-locale LANG=C.UTF-8 LC_MESSAGES=POSIX \
 && locale-gen en_US.UTF-8 \
 && dpkg-reconfigure -f noninteractive locales \
 && echo "Europe/Paris" >/etc/timezone \
 && dpkg-reconfigure -f noninteractive tzdata \
 && rm -rf /var/lib/apt/lists/*

ADD assets/setup/ /app/setup/
ADD assets/config/ /app/setup/config/
# @BUIAGENT_ARTIFACTS@
# @BUIMONITOR_ARTIFACTS@

ADD assets/init /app/init
RUN chmod 755 /app/init

RUN chmod 755 /app/setup/install
RUN /app/setup/install

EXPOSE 10000/tcp

VOLUME ["/srv/demo/spool/burp2/backup:/var/spool/burp"]
VOLUME ["/srv/demo/spool/burp2/tmp:/tmp/bui"]

ENTRYPOINT ["/app/init"]
CMD ["app:start"]
