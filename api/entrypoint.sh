#!/bin/sh
set -e

python wait_for_db.py

# Gera migrations na primeira vez que o schema muda (idempotente).
# Em produção, prefira commitar as migrations no repo e rodar só `migrate`.
python manage.py makemigrations --no-input
python manage.py migrate --no-input
python manage.py seed_categories
python manage.py collectstatic --no-input --clear

exec "$@"
