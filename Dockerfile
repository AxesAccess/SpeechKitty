FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg

# We need full access to mounted directory
USER root

WORKDIR /root/

COPY app app
COPY pyproject.toml pyproject.toml
COPY sample sample

RUN pip install .