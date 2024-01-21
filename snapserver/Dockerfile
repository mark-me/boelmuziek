FROM alpine:3.19.0

RUN apk add snapcast-server && \
    mkdir -p /var/lib/snapserver/soundshare

COPY ./snapserver.conf /var/lib/snapserver/snapserver.conf

EXPOSE 1704

ENTRYPOINT ["/usr/bin/snapserver"]