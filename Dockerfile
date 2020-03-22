FROM python:3.8.1-slim

ENV PYTHONPATH=/app

RUN mkdir /app
COPY requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt

# copy everything else after pip install to take advantage of docker image layers (cache)
COPY . /app

WORKDIR /app
