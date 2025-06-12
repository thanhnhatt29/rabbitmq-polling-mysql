# docker file poller
FROM python:3.11-slim

WORKDIR /app

COPY poller.py .

RUN pip install pika mysql-connector-python

CMD ["python", "poller.py"]