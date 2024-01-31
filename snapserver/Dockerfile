FROM alpine:3.19.0

RUN apk add snapcast-server --no-cache \
    && mkdir -p /var/lib/snapserver/soundshare

RUN apk add --no-cache openrc \
    && apk add --no-cache avahi \
    && apk add --no-cache dbus \
    && apk add --no-cache tzdata

RUN apk add -U avahi \
    && apk add dbus \
    && dbus-uuidgen > /var/lib/dbus/machine-id \
    && mkdir -p /var/run/dbus \
    && rm -rf /etc/ssl /var/cache/apk/* /lib/apk/db/*

COPY ./snapserver.conf /etc/snapserver.conf

EXPOSE 1704
EXPOSE 1705
# Volume control
EXPOSE 1780

#ENTRYPOINT ["/usr/bin/snapserver"]
CMD dbus-daemon --config-file=/usr/share/dbus-1/system.conf --print-address; avahi-daemon -D; snapserver

