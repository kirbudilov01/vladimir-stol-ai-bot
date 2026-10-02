FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY webapp ./webapp
RUN mkdir -p /app/data /app/storage
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD python -m app.healthcheck || exit 1

CMD ["python", "-m", "app.main"]
