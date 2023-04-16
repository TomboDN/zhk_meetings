FROM python:3.11.2-slim

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update -y \
    && apt-get upgrade -y \
    && apt-get install -y postgresql postgresql-contrib gcc python3-dev musl-dev \
    && apt-get install --reinstall libpq-dev \
    && apt-get install -y netcat \
    && apt-get install -y libreoffice-writer \
    && apt-get install -y unoconv

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY ./entrypoint.sh .
RUN sed -i 's/\r$//g' /usr/src/app/entrypoint.sh
RUN chmod +x /usr/src/app/entrypoint.sh

COPY . .

ENTRYPOINT ["/bin/sh", "/usr/src/app/entrypoint.sh"]