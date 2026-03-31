# Webhook SaaS (multiempresa)

Backend em **FastAPI** + **PostgreSQL**: cadastro de empresas, números WhatsApp (Uazapi), geração estável de webhook por número, recepção de eventos e API para integrações.

Documento de requisitos: `PROMPT-ARQUITETURA.md`.

## Requisitos

- Python 3.11+
- PostgreSQL 16+ (ou use `docker compose up -d`)

## Configuração

1. Copie `.env.example` para `.env` e ajuste `SECRET_KEY`, `AUTH_CLIENT_SECRET` e `DATABASE_URL`.
2. Crie o schema:

```bash
alembic upgrade head
```

3. Suba o servidor:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. Obtenha token de gestão:

```http
POST /api/v1/auth/token
Content-Type: application/json

{"client_id": "admin", "client_secret": "<AUTH_CLIENT_SECRET>"}
```

Use `Authorization: Bearer <access_token>` nas rotas de empresas e números.

## Endpoints principais

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/auth/token` | Token JWT (gestão) |
| POST/GET/PATCH | `/api/v1/companies` | CRUD empresas |
| POST | `/api/v1/companies/{id}/phone-numbers` | Cria número + gera webhook (retorna URL completa uma vez) |
| GET | `/api/v1/companies/{id}/phone-numbers` | Lista números |
| GET | `/api/v1/companies/{id}/phone-numbers/{pid}` | Detalhe (URL completa não reexibida) |
| GET | `/api/v1/companies/{id}/phone-numbers/{pid}/webhook` | Prefixo + mensagem |
| POST | `/api/v1/companies/{id}/phone-numbers/{pid}/webhook/regenerate` | Novo token + nova URL |
| POST | `/api/v1/phone-numbers/{id}/webhook/regenerate` | Idem (atalho) |
| * | `/api/v1/webhooks/whatsapp/{company_id}/{phone_number_id}/{token}` | Recebimento Uazapi (público) |

O token do webhook é armazenado apenas como **hash**; a URL completa só aparece na criação do número ou após regeneração.

## Testes

```bash
python -m pytest tests/ -v
```

Os testes usam SQLite em arquivo temporário (não exigem PostgreSQL).

## Variáveis de ambiente

Ver `.env.example`.

## Publicar no GitHub

Repositório remoto sugerido: [farollapi-cloud/webhook](https://github.com/farollapi-cloud/webhook).

```bash
git remote add origin https://github.com/farollapi-cloud/webhook.git   # se ainda não existir
git push -u origin main
```

Se aparecer **403 Permission denied**, a conta Git no PC não tem permissão de escrita na organização. Use uma conta com acesso ao org, um **Personal Access Token** com escopo `repo` ao usar HTTPS, ou configure **SSH** (`git@github.com:farollapi-cloud/webhook.git`) com chave autorizada no GitHub.
