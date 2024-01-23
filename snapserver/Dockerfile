FROM alpine:3.19.0

RUN apk add snapcast-server \
    && apk add avahi \
    && mkdir -p /var/lib/snapserver/soundshare

COPY ./snapserver.conf /var/lib/snapserver/snapserver.conf

EXPOSE 1704
EXPOSE 1705

ENTRYPOINT ["/usr/bin/snapserver"]