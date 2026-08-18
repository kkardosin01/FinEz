#!/bin/sh
set -e

python wait_for_db.py

# Worker/beat não rodam migrate (evita corrida entre containers) — o serviço
# `api` é responsável por aplicar migrations e seed no boot.
echo "Aguardando o serviço api aplicar migrations..."
until python manage.py migrate --check >/dev/null 2>&1; do
  sleep 2
done

exec "$@"
