FROM python:3.12-slim

RUN pip install --no-cache-dir pyzmq==27.1.*

WORKDIR /app
COPY relay.py /app/relay.py

ENTRYPOINT ["python3", "-u", "/app/relay.py"]
