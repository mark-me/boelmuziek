FROM alpine:3.19.0

ARG user=icecast
ARG group=icecast

RUN apk -q update \
    && apk --no-cache add icecast \
    && apk --no-cache add tzdata

COPY silence.ogg /usr/share/icecast/silence.ogg
COPY icecast.xml /usr/share/icecast/icecast.xml

RUN mkdir -p /var/log/icecast \
    && chown -R ${user}:${group} /usr/share/icecast \
    && chown -R ${user}:${group} /var/log/icecast

EXPOSE 8000

USER ${user}
CMD ["icecast", "-c", "/usr/share/icecast/icecast.xml"]
