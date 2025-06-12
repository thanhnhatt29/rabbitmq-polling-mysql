# docker file consumer
FROM python:3.11-slim

WORKDIR /app

COPY consumer.py .

RUN apt-get update && apt-get install -y unixodbc-dev gcc g++ gnupg \
 && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
 && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
 && apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
 && pip install pika pyodbc

CMD ["python", "consumer.py"]
