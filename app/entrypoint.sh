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

python manage.py flush --no-input
python manage.py makemigrations
python manage.py migrate

exec "$@"