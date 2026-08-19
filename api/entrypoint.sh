#!/bin/sh
set -e

python wait_for_db.py

# Migrations são commitadas no repo (ver api/*/migrations/) — só aplica.
python manage.py migrate --no-input
python manage.py seed_categories
python manage.py collectstatic --no-input --clear

exec "$@"
