#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

find ./zhk_meetings_app/migrations -type f -not -name '__init__.py' -delete
sleep 1

export PGPASSWORD=$SQL_PASSWORD 

psql -d postgres -U zhk_meetings -h $SQL_HOST -p $SQL_PORT -c 'drop database zhk_db;' -c 'create database zhk_db;'

python manage.py flush --no-input
python manage.py makemigrations
python manage.py migrate
sleep 1
python manage.py loaddata data.json
python manage.py collectstatic

cp /usr/lib/python3/dist-packages/unohelper.py /usr/lib/libreoffice/program
cp /usr/lib/python3/dist-packages/uno.py /usr/lib/libreoffice/program

exec "$@"