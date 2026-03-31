# Webhook SaaS (multiempresa)

Backend em **FastAPI** + **PostgreSQL** e **frontend** em **React (Vite)**: cadastro de empresas, números WhatsApp (Uazapi), webhooks e painel web.

Documento de requisitos: `PROMPT-ARQUITETURA.md`.

## Requisitos

- Python 3.11+
- Node 20+ (para o frontend)
- PostgreSQL 16+ local (ou `docker compose up -d`)

## Backend (local)

1. Copie `.env.example` para `.env` e ajuste `SECRET_KEY`, `AUTH_CLIENT_SECRET`, `DATABASE_URL` e `CORS_ORIGINS` (ex.: `http://localhost:5173`).
2. Migrações:

```bash
alembic upgrade head
```

3. API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. Token de gestão: `POST /api/v1/auth/token` com `client_id` e `client_secret` (ver `.env.example`).

## Frontend (local)

```bash
cd frontend
cp .env.example .env
# Edite VITE_API_URL se a API não estiver em http://localhost:8000
npm install
npm run dev
```

Abra o endereço indicado pelo Vite (geralmente `http://localhost:5173`). Faça login com as mesmas credenciais `AUTH_CLIENT_ID` / `AUTH_CLIENT_SECRET` da API.

## Deploy na Render (API + Static Site + Postgres)

O repositório inclui [`render.yaml`](render.yaml) (Blueprint): **webhook-api** (Python), **webhook-web** (site estático) e **webhook-db** (PostgreSQL).

1. No [Render Dashboard](https://dashboard.render.com), crie um **Blueprint** apontando para este repositório (arquivo `render.yaml` na raiz).
2. No primeiro deploy, o painel pedirá valores para variáveis `sync: false`:
   - **`CORS_ORIGINS`**: URL pública do site estático (ex.: `https://webhook-web.onrender.com`). Sem barra final.
   - **`VITE_API_URL`**: URL pública **da API** (ex.: `https://webhook-api.onrender.com`). Sem barra final. O build do frontend embute esse valor.
3. A API usa automaticamente **`RENDER_EXTERNAL_URL`** (injetada pela Render) para montar URLs de webhook quando `BACKEND_PUBLIC_URL` não foi definido — ou seja, os webhooks da Uazapi devem apontar para a **URL do serviço `webhook-api`**, não do static site.
4. Após o primeiro deploy da API, copie a URL pública do **webhook-api**, preencha `VITE_API_URL` e `CORS_ORIGINS` e faça **redeploy** do **webhook-web** se necessário.

Limites do [plano gratuito](https://render.com/docs/free): serviço web pode hibernar após inatividade; Postgres free expira em 90 dias (ver documentação atual da Render).

### Login no site dá erro / “Falha ao conectar”

São **dois serviços** (API e Static Site). O login do navegador chama a **API** usando a URL gravada no **build** do frontend.

1. **No Static Site** (não na API): variável **`VITE_API_URL`** = URL **https** do **Web Service da API** (ex.: `https://webhook-api.onrender.com`), **sem barra no final**. Depois de alterar, faça **novo deploy** do Static Site (o Vite embute o valor na hora do build).
2. **No Web Service da API**: variável **`CORS_ORIGINS`** = URL **https** do **Static Site** (ex.: `https://webhook-frontend-pb6s.onrender.com`), **sem barra no final**. Salve e redeploy/restart se precisar.
3. **No Web Service da API**: **`AUTH_CLIENT_ID`** e **`AUTH_CLIENT_SECRET`** = os mesmos valores que você digita na tela de login.

Na tela de login, o texto **“Chamadas vão para: …”** mostra qual URL o site está usando. Se aparecer `localhost`, o `VITE_API_URL` não foi definido no build do Static Site.

## Endpoints principais (API)

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/auth/token` | Token JWT (gestão) |
| POST/GET/PATCH | `/api/v1/companies` | CRUD empresas |
| POST | `/api/v1/companies/{id}/phone-numbers` | Cria número + gera webhook |
| GET | `/api/v1/companies/{id}/phone-numbers` | Lista números |
| GET | `/api/v1/companies/{id}/phone-numbers/{pid}` | Detalhe |
| POST | `.../webhook/regenerate` | Novo token + nova URL |
| * | `/api/v1/webhooks/whatsapp/...` | Recebimento Uazapi (público) |

## Testes (backend)

```bash
python -m pytest tests/ -v
```

## Variáveis de ambiente

- Raiz: `.env.example`
- Frontend: `frontend/.env.example`

## Publicar no GitHub

```bash
git remote add origin https://github.com/farollapi-cloud/webhook.git
git push -u origin main
```

Se aparecer **403**, verifique permissões na organização ou use PAT/SSH.
