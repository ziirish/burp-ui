FROM registry.ziirish.me/ziirish/burp-ui:demo

ADD assets/config/ /app/setup/config/
ADD assets/init /app/init 

RUN chmod 755 /app/init

ENTRYPOINT ["/app/init"]
CMD ["app:start"]
