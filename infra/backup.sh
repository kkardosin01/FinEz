#!/bin/sh
# Backup noturno: pg_dump + cópia pra fora do VPS (Cloudflare R2 ou Backblaze B2).
# Backup que mora só no servidor não é backup — testar o restore antes do primeiro usuário.
#
# Agendar via cron no host (fora do Compose), ex.:
#   0 3 * * * /opt/finez/infra/backup.sh >> /var/log/finez-backup.log 2>&1
#
# Requer: aws-cli configurado com endpoint do R2/B2 (variáveis de ambiente
# AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, BACKUP_S3_ENDPOINT, BACKUP_S3_BUCKET).
set -eu

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
DUMP_FILE="/tmp/finez-${TIMESTAMP}.sql.gz"

docker compose exec -T postgres pg_dump -U "${POSTGRES_USER:-finez}" "${POSTGRES_DB:-finez}" \
  | gzip > "$DUMP_FILE"

aws s3 cp "$DUMP_FILE" "s3://${BACKUP_S3_BUCKET}/finez/${TIMESTAMP}.sql.gz" \
  --endpoint-url "${BACKUP_S3_ENDPOINT}"

rm -f "$DUMP_FILE"
echo "Backup ${TIMESTAMP} enviado com sucesso."
