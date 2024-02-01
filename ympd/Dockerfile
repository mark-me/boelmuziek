FROM alpine:3.19.0

RUN apk --no-cache add ympd  \
    && apk --no-cache add tzdata

EXPOSE 8080

CMD ["ympd", "-h", "mpd", "-p", "6600", "-w", "8080"]
