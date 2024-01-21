FROM python:3.9.18-slim-bookworm

WORKDIR /app
COPY ./requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 5000

CMD ["uvicorn", "main:app", "--reload", "--port", "5000"]
