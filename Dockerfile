FROM python:3.9-slim as builder

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg

# I know it's not secure but we need full access to mounted directory
USER root

WORKDIR /root/

COPY . .

RUN pip install .