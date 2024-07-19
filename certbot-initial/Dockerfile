# See https://eff-certbot.readthedocs.io/en/latest/install.html#running-with-docker
FROM certbot/certbot:latest

COPY certbot-initial-entrypoint.sh certbot-initial-entrypoint.sh

ENTRYPOINT sh ./certbot-initial-entrypoint.sh