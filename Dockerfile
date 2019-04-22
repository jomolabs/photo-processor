FROM python:3.7.2-alpine3.9

RUN mkdir /app
WORKDIR /app

RUN apk add --no-cache build-base jpeg-dev zlib-dev postgresql-dev supervisor

RUN pip install pipenv

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

RUN pipenv install --deploy --system

COPY scripts scripts
COPY src src
COPY supervisord.conf /etc/supervisord.conf

CMD scripts/start.sh
