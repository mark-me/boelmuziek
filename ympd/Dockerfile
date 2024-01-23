FROM alpine:3.19.0

RUN apk add ympd

EXPOSE 8080

CMD ["ympd", "-h", "mpd", "-p", "6600", "-w", "8080"]
