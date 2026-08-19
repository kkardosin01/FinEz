# FinEz

*Financial easy* — app de finanças pessoais pra jovens de 16 a 25 anos, com o
**WhatsApp como interface diária** (lançar/consultar gastos por mensagem) e
**Open Finance opcional** (Pluggy) pra importar extratos automaticamente.

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat&logo=typescript&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat&logo=javascript&logoColor=black)
![Django](https://img.shields.io/badge/Django-092E20?style=flat&logo=django&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=flat&logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-339933?style=flat&logo=node.js&logoColor=white)

## Stack

| Camada | Tecnologia |
|---|---|
| API | Django 5 + DRF + drf-spectacular (OpenAPI), PostgreSQL 16, Celery + Redis |
| Front | React 18 + Vite + TypeScript, Tailwind, TanStack Query, Zustand, React Hook Form + Zod |
| Bot | Node 20 + Baileys (WhatsApp Web protocol), sessão persistida com AES-256-GCM |
| Agregador Open Finance | Pluggy (sandbox gratuito em desenvolvimento) |
| Infra | Docker Compose, Caddy (TLS automático), GitHub Actions (CI/CD) |

## Linguagens

| Linguagem | Onde |
|---|---|
| Python | API (`api/`) — Django, Celery |
| TypeScript | Front (`web/`) — React |
| JavaScript | Adaptador WhatsApp (`whatsapp-adapter/`) — Node/Baileys |
| SQL | Modelos/migrations do Django (ORM) |
| Shell | Scripts de entrypoint e backup (`api/entrypoint*.sh`, `infra/backup.sh`) |
| YAML | CI/CD (`.github/workflows/`), Docker Compose |

## Estrutura

```
finez/
├── api/                  # Django (accounts, transactions, connections, budgets, whatsapp, exports)
├── web/                  # React (SPA + PWA)
├── whatsapp-adapter/     # Node/Baileys — ponte entre WhatsApp e a API
├── infra/                # Caddyfile, script de backup
├── .github/workflows/    # CI/CD
├── docker-compose.yml
└── .env.example
```

## Setup local (Docker Compose — recomendado)

1. Copie o arquivo de ambiente e preencha os segredos:
   ```sh
   cp .env.example .env
   ```
   Gere as chaves obrigatórias:
   ```sh
   # Fernet (criptografa tokens do Pluggy)
   python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   # Sessão do WhatsApp (AES-256-GCM)
   openssl rand -hex 32
   ```
   Preencha `FERNET_KEY` e `WHATSAPP_SESSION_KEY` no `.env` com os valores gerados.
   `PLUGGY_CLIENT_ID`/`PLUGGY_CLIENT_SECRET` só são necessários pra testar a
   conexão bancária de verdade — sem eles, o resto do app funciona normalmente
   (o fluxo de conexão bancária mostra uma mensagem de "indisponível").

2. Suba os serviços:
   ```sh
   docker compose up --build
   ```
   No primeiro boot, o container `api` roda `makemigrations` + `migrate` +
   `seed_categories` automaticamente (ver `api/entrypoint.sh`). Os workers
   (`worker`/`beat`) esperam essa migração terminar antes de subir.

3. Abra:
   - App: http://localhost (via Caddy) ou http://localhost:5173 (`npm run dev`, ponto 4)
   - API docs (Swagger): http://localhost:8000/api/docs/
   - Admin Django: http://localhost:8000/admin/

4. Crie um convite pra poder se cadastrar (o cadastro é fechado por convite):
   ```sh
   docker compose exec api python manage.py shell -c \
     "from accounts.models import Invite; print(Invite.objects.create(code='FINEZ-A3X9', max_uses=1).code)"
   ```

### Rodando o front fora do Compose (hot reload mais rápido)

```sh
cd web
npm install
npm run dev   # http://localhost:5173, aponta pra VITE_API_URL=http://localhost:8000
```

## Testes

```sh
# Backend (requer Postgres/Redis — via Compose ou local)
cd api
pip install -r requirements-dev.txt
pytest

# Frontend
cd web
npm run lint
npm run build
```

## Backup

`infra/backup.sh` faz `pg_dump` + upload pra um bucket S3-compatible (R2/B2).
Agende no host via cron (fora do Compose):

```
0 3 * * * /opt/finez/infra/backup.sh >> /var/log/finez-backup.log 2>&1
```

Requer `aws-cli` configurado e as variáveis `AWS_ACCESS_KEY_ID`,
`AWS_SECRET_ACCESS_KEY`, `BACKUP_S3_ENDPOINT`, `BACKUP_S3_BUCKET` no
ambiente do host. **Teste o restore antes do primeiro usuário real** — backup
que nunca foi restaurado não é backup.

## CI/CD

`.github/workflows/deploy.yml`: em todo push/PR roda lint + testes de
`api` e `web`; em push pra `main`, se os testes passarem, conecta via SSH na
VPS (`secrets.VPS_HOST/VPS_USER/VPS_SSH_KEY`), dá `git pull` e recria os
containers (`docker compose build && up -d`).

## Pendências conhecidas / stubs

Este é o scaffold completo do MVP descrito na especificação, incluindo bot e
integração Pluggy — mas alguns pontos dependem de credenciais reais ou
decisões de produto que ficam pra depois do beta:

- **Fallback LLM do parser do WhatsApp**: a heurística (regex + palavras-chave)
  cobre lançamento/consulta/correção; o fallback pra LLM quando a heurística
  falha está com a integração pendente (`LLM_PROVIDER`/`LLM_API_KEY` no
  `.env` — sem eles, mensagens não reconhecidas caem em "não entendi").
- **Credenciais Pluggy**: sandbox configurado (`PLUGGY_CLIENT_ID`/`SECRET` no
  `.env`). Sem elas, o botão "conectar banco" mostra uma mensagem de
  indisponibilidade em vez de quebrar.
- **Widget do Pluggy Connect**: versão confirmada em uso (`v2.11.0`, igual
  ao alias `latest` do CDN deles) em `web/src/features/connections/useConnectFlow.ts`
  — reconfirme periodicamente, já que a Pluggy descontinua versões antigas sem aviso.
- **Ícones do PWA** (`web/public/icon-*.png`): placeholders sólidos na cor da
  marca — trocar por artes reais antes do lançamento.
- **Migrations do Django**: não foram commitadas à mão (evita erro humano em
  ~10 modelos relacionados); são geradas automaticamente no primeiro boot do
  container `api`. Em produção, prefira gerá-las localmente com Postgres real
  e commitá-las no repo, rodando só `migrate` no deploy.
- **Categorias/paleta de cores** (`api/transactions/management/commands/seed_categories.py`):
  cores placeholder, pendente validação de design.

## Licença

Projeto privado — uso interno.
