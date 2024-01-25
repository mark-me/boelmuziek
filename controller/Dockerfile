FROM python:3.9.18-slim-bookworm

WORKDIR /app
COPY ./requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY . .
COPY static/ .

EXPOSE 5000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
