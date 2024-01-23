FROM alpine:3.19.0

RUN apk add snapcast-server --no-cache \
    && mkdir -p /var/lib/snapserver/soundshare

RUN apk add openrc --no-cache \
    && apk add avahi --no-cache \
    && apk add dbus --no-cache

RUN rc-update add avahi-daemon \
    && rc-update add dbus
#\
#    && rc-service avahi-daemon start

COPY ./snapserver.conf /etc/snapserver.conf

EXPOSE 1704
EXPOSE 1705
# Volume control
EXPOSE 1780

ENTRYPOINT ["/usr/bin/snapserver"]