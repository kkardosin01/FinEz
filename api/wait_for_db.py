"""Espera o Postgres aceitar conexões antes de seguir com migrate/gunicorn."""
import sys
import time

import environ

env = environ.Env()
environ.Env.read_env(".env")

db_config = env.db("DATABASE_URL", default="postgres://finez:finez@localhost:5432/finez")

import psycopg  # noqa: E402

max_attempts = 30
for attempt in range(1, max_attempts + 1):
    try:
        conn = psycopg.connect(
            host=db_config["HOST"],
            port=db_config["PORT"] or 5432,
            dbname=db_config["NAME"],
            user=db_config["USER"],
            password=db_config["PASSWORD"],
            connect_timeout=3,
        )
        conn.close()
        print("Banco de dados disponível.")
        sys.exit(0)
    except Exception as exc:
        print(f"Aguardando o banco ({attempt}/{max_attempts})... {exc}")
        time.sleep(2)

print("Banco de dados indisponível após várias tentativas.", file=sys.stderr)
sys.exit(1)
