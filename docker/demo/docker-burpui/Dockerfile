FROM registry.ziirish.me/ziirish/burp-ui:demo
MAINTAINER hi+burpui@ziirish.me

ADD assets/config/ /app/setup/config/
ADD assets/init /app/init 

RUN chmod 755 /app/init

ENTRYPOINT ["/app/init"]
