FROM python:3.4
MAINTAINER ziirish@ziirish.info

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y locales wget curl uthash-dev g++ make libssl-dev librsync-dev python3.4-dev \ 
 && update-locale LANG=C.UTF-8 LC_MESSAGES=POSIX \
 && locale-gen en_US.UTF-8 \
 && dpkg-reconfigure -f noninteractive locales \
 && echo "Europe/Paris" >/etc/timezone \
 && dpkg-reconfigure -f noninteractive tzdata \
 && rm -rf /var/lib/apt/lists/*

CMD ["/usr/bin/python"]
