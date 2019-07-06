FROM python:3.7-slim

ENV PYTHONUNBUFFERED 1

COPY requirements.txt /shop_bot/requirements.txt
RUN pip install -r /shop_bot/requirements.txt

COPY ./src/ /shop_bot/src/


WORKDIR /shop_bot/
