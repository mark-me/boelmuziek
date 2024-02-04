FROM python:3.9.18-slim-bookworm

WORKDIR /app
RUN mkdir config
RUN mkdir artist_images
COPY ./requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . .
RUN rm .env

VOLUME /app/config
VOLUME /app/artist_images

EXPOSE 5000

CMD ["./entrypoint.sh"]
