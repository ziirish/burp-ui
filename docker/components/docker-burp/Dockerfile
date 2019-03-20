FROM alpine:3.7

RUN apk add --no-cache supervisor logrotate librsync libressl tzdata bash coreutils \
	&& apk add --no-cache --virtual .fetch-deps \
		tar \
	\
	&& wget -O burp.tar.gz https://github.com/grke/burp/archive/2.2.18.tar.gz \
	&& wget -O uthash.tar.gz https://github.com/troydhanson/uthash/archive/v2.1.0.tar.gz \
	&& mkdir -p /usr/src/burp /usr/src/uthash \
	&& tar -xC /usr/src/burp --strip-components=1 -f burp.tar.gz \
	&& tar -xC /usr/src/uthash --strip-components=1 -f uthash.tar.gz \
	&& rm burp.tar.gz uthash.tar.gz \
	\
	&& apk add --no-cache --virtual .build-deps \
		g++ \
		libc-dev \
		make \
		libressl-dev \
		zlib-dev \
		librsync-dev \
		pkgconfig \
		yajl-dev \
		autoconf \
		automake \
		libtool \
	\
# add build deps before removing fetch deps in case there's overlap
	&& apk del .fetch-deps \
	\
	&& cd /usr/src/burp \
	&& autoreconf -vif \
	&& CPPFLAGS="-I../uthash/src" ./configure \
		--prefix=/usr \
		--sysconfdir=/etc/burp \
		--localstatedir=/var \
	&& make -j \
	&& make install \
	&& make install-configs \
	\
	&& runDeps="$( \
		scanelf --needed --nobanner --recursive /usr/local \
			| awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
			| sort -u \
			| xargs -r apk info --installed \
			| sort -u \
	)" \
	&& apk add --virtual .python-rundeps $runDeps \
	&& apk del .build-deps \
# do some cleanup
	&& rm -rf /usr/src/burp /usr/src/uthash ~/.cache

ADD assets/init /app/init
ADD assets/setup/ /app/setup/

RUN chmod 755 /app/init
RUN chmod 755 /app/setup/install
RUN /app/setup/install

EXPOSE 4971/tcp
EXPOSE 4972/tcp

VOLUME ["/var/spool/burp"]
VOLUME ["/etc/burp"]

ENTRYPOINT ["/app/init"]
CMD ["app:start"]
