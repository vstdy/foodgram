#!/bin/sh
set -e

while ! nc -w 1 -zv db 5432; do sleep 1; done
python manage.py migrate --noinput
python manage.py loaddata fixtures.json
python manage.py collectstatic --noinput

exec "$@"
