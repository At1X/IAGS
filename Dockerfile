FROM python:3.8.3-slim-buster

RUN mkdir interkarsolar
WORKDIR /interkarsolar
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

