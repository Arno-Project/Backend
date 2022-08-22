FROM python:3.10.4-slim-bullseye

WORKDIR /app

LABEL maintainer="amirmahdi.namjoo1@gmail.com"
LABEL description="Development image for Arno Project"
LABEL authors="Saba Hashemi - Amirmahdi Namjoo - Mostafa Ojaghi  - Alireza Tajmirriahi"

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update \
    && apt-get -y install netcat gcc postgresql iputils-ping net-tools \
    && apt-get clean

RUN apt-get update \
    && apt-get install -y binutils libproj-dev gdal-bin python3-gdal

RUN pip install --upgrade pip

COPY ./requirements.txt /app/requirements.txt

RUN pip install -r requirements.txt

COPY . /app
