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

# add custom sql functions to db 
#cat ./sql/fill_tables.sql | python manage.py dbshell
#python manage.py collectstatic --no-input

psql -d postgres -U zhk_meetings -h $SQL_HOST -p $SQL_PORT -W -d zhk_db
psql -d postgres -U zhk_meetings -h $SQL_HOST -p $SQL_PORT -f ./sql/fill_tables.sql

exec "$@"