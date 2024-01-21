FROM alpine:3.19.0

RUN apk add snapcast-server && \
    mkdir -p /var/lib/snapserver/soundshare

EXPOSE 1704

ENTRYPOINT ["/usr/bin/snapserver"]