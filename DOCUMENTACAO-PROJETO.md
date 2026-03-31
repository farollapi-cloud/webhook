# Documentação do projeto — Webhook SaaS (multiempresa)

Este documento descreve **o que foi construído**, **onde está cada coisa**, **variáveis de ambiente**, **links (GitHub e Render)** e **como tudo se conecta**.  
Substitua os exemplos de URL da Render pelos **seus** endereços reais (cada deploy gera um subdomínio).

---

## 1. Repositório no GitHub

| Item | Valor |
|------|--------|
| **Organização / repositório** | `farollapi-cloud/webhook` |
| **URL pública do código** | `https://github.com/farollapi-cloud/webhook` |
| **Branch principal** | `main` |

O código-fonte (backend FastAPI, pasta `frontend/`, `render.yaml`, testes, migrações Alembic) é versionado nesse repositório.  
**Não** commite arquivo `.env` com segredos reais (ele está no `.gitignore`).

---

## 2. O que este sistema faz (resumo funcional)

1. **Cadastrar empresas** (dados cadastrais, status, observações).  
2. **Cadastrar números de WhatsApp** por empresa, vinculados à Uazapi (URL base + token da instância).  
3. **Gerar automaticamente um webhook exclusivo por número** (URL com token secreto).  
4. **Exibir** prefixo ou URL completa (na criação/regeneração) para colar no painel da Uazapi.dev.  
5. **Receber eventos** POST da Uazapi no endpoint público, validar, gravar log e responder rápido.  
6. **Painel web** (React) para login, empresas, números, copiar URL/regenerar webhook.

**Fora de escopo** (por desenho): CRM, chatbot, IA, relatórios pesados, processamento de mensagens além de persistir o payload.

---

## 3. Arquitetura na Render (três peças)

Na Render este projeto foi pensado para **três recursos** (definidos no [`render.yaml`](render.yaml)):

| Recurso | Serviço na Render | Função |
|---------|-------------------|--------|
| **Banco PostgreSQL** | Nome no blueprint: `webhook-db` | Guarda empresas, números, config de webhook, logs de eventos. |
| **Web Service (API)** | Nome no blueprint: `webhook-api` | Roda **FastAPI** (`uvicorn`), expõe `/api/v1/...`, `/health` e o webhook público. |
| **Site estático** | Nome no blueprint: `webhook-web` | Build do **React (Vite)** em `frontend/`, servido como CDN. |

Fluxo lógico:

```
Navegador  →  Static Site (frontend React)
     ↓ HTTPS + JSON
Web Service (API FastAPI)  →  PostgreSQL
     ↑
Uazapi.dev (webhooks POST)  →  mesma API (endpoint público com token na URL)
```

- **Login e CRUD** no painel: o navegador chama **só a API** (não o Static Site para dados).  
- **Webhooks da Uazapi** devem apontar para a **URL do Web Service da API**, não para o Static Site.

---

## 4. Endereços na Render (como preencher)

A Render gera **subdomínios únicos** no formato `https://<nome-do-serviço>.onrender.com`.  
Os nomes **exatos** aparecem no painel de cada serviço (aba **Settings** ou no topo da página do serviço).

### 4.1 Tabela de papéis (você preenche com seus links)

| Papel | Onde configurar | Exemplo de formato (não copie como verdade absoluta) |
|-------|-----------------|--------------------------------------------------------|
| **URL do site (painel)** | Navegador do usuário | `https://<seu-static>.onrender.com` |
| **URL da API (backend)** | `VITE_API_URL` no **Static Site**; Uazapi aponta webhooks aqui | `https://<seu-web-service-api>.onrender.com` |
| **URL da API (automática)** | Render injeta `RENDER_EXTERNAL_URL` no Web Service da API | Igual à URL pública da API (usada no código para montar links de webhook) |

**Exemplo real citado durante o projeto** (pode ser diferente do seu deploy atual):

- Frontend: `https://webhook-frontend-pb6s.onrender.com`  
- API: você deve usar o **URL que a Render mostra** na Web Service da API (ex.: `https://webhook-api.onrender.com` ou nome que você escolheu).

**Regra:** sempre **HTTPS** nas URLs públicas. **Sem barra** `/` no final ao configurar `VITE_API_URL` e `CORS_ORIGINS`.

---

## 5. Variáveis de ambiente (completo)

### 5.1 API (Web Service) — backend Python

| Variável | Obrigatória? | Descrição |
|----------|----------------|-----------|
| `DATABASE_URL` | Sim | Conexão PostgreSQL. No Blueprint vem do banco `webhook-db` (`connectionString`). |
| `SECRET_KEY` | Sim | Chave para assinar JWT. No Blueprint pode ser `generateValue: true`. |
| `AUTH_CLIENT_ID` | Sim | “Login” da API de gestão (ex.: `admin`). Padrão no Blueprint: `admin`. |
| `AUTH_CLIENT_SECRET` | Sim | “Senha” da API de gestão. No Blueprint pode ser gerada; você vê no painel. |
| `ENVIRONMENT` | Recomendado | `production` na Render. |
| `LOG_LEVEL` | Opcional | Ex.: `INFO`. |
| `CORS_ORIGINS` | **Sim em produção** | Lista separada por **vírgula** com a(s) URL(s) **https** do(s) site(s) que podem chamar a API. Ex.: `https://<seu-static>.onrender.com`. Sem barra no final. |
| `BACKEND_PUBLIC_URL` | Opcional | Fallback local/dev. Na Render a API usa **`RENDER_EXTERNAL_URL`** (injetada) para montar URLs de webhook quando disponível. |
| `WEBHOOK_MAX_BODY_BYTES` | Opcional | Tamanho máximo do body no POST do webhook (padrão no código: 512 KiB). |
| `RENDER_EXTERNAL_URL` | Automática | Injetada pela Render no Web Service — **não** precisa criar manualmente. Usada em [`app/config.py`](app/config.py) para `resolved_public_base_url()`. |

**Arquivo de referência local:** [`.env.example`](.env.example).

### 5.2 Static Site (frontend) — build do Vite

| Variável | Obrigatória? | Descrição |
|----------|----------------|-----------|
| `VITE_API_URL` | **Sim** | URL **HTTPS** da **API** (Web Service), **sem** `/` no final. É embutida no JavaScript no **momento do build**. Se faltar, o app tenta `http://localhost:8000` e o login na internet **quebra**. |

**Arquivo de referência:** [`frontend/.env.example`](frontend/.env.example).

### 5.3 Desenvolvimento local (frontend)

Crie `frontend/.env` (não commitado) com:

```env
VITE_API_URL=http://localhost:8000
```

---

## 6. O que foi implementado no código (por área)

### 6.1 Backend (FastAPI)

- **App:** [`app/main.py`](app/main.py) — `CORSMiddleware`, rotas `/api/v1`, `/health`.  
- **Config:** [`app/config.py`](app/config.py) — leitura de env; `resolved_public_base_url()` usa `RENDER_EXTERNAL_URL` ou `BACKEND_PUBLIC_URL`.  
- **Modelos:** `Company`, `PhoneNumber`, `WebhookConfig`, `WebhookEventLog` em [`app/models/`](app/models/).  
- **Migrações:** Alembic em [`alembic/versions/`](alembic/versions/).  
- **Auth:** JWT em `POST /api/v1/auth/token` ([`app/api/v1/auth.py`](app/api/v1/auth.py)).  
- **CRUD empresas:** [`app/api/v1/companies.py`](app/api/v1/companies.py).  
- **Números e webhooks:** [`app/api/v1/phone_numbers.py`](app/api/v1/phone_numbers.py).  
- **Webhook inbound (Uazapi):** [`app/api/v1/inbound.py`](app/api/v1/inbound.py) — validação, log, 404 em falha; 200 em sucesso.  
- **Segurança:** token do path gerado com `secrets.token_urlsafe`, armazenado como hash SHA-256; comparação com `hmac.compare_digest` ([`app/security.py`](app/security.py)).

### 6.2 Frontend (React + Vite + Tailwind)

- **Pasta:** [`frontend/`](frontend/).  
- **Telas:** login, lista/criação de empresas, detalhe da empresa (números, copiar prefixo/URL, regenerar).  
- **Cliente HTTP:** [`frontend/src/lib/api.ts`](frontend/src/lib/api.ts) — usa `VITE_API_URL`.  
- **Build:** `npm run build` → saída em `frontend/dist/`.

### 6.3 Infraestrutura como código

- [`render.yaml`](render.yaml) — Postgres `webhook-db`, serviços `webhook-api` e `webhook-web`, variáveis com `sync: false` onde o painel precisa pedir valor manualmente (`CORS_ORIGINS`, `VITE_API_URL`).

### 6.4 Documentação e testes

- [`README.md`](README.md) — uso local, deploy, troubleshooting de login.  
- [`PROMPT-ARQUITETURA.md`](PROMPT-ARQUITETURA.md) — especificação original do produto.  
- Testes [`tests/`](tests/) — pytest com SQLite em arquivo temporário.

---

## 7. Endpoints principais da API

| Método | Caminho | Autenticação | Descrição |
|--------|---------|----------------|-----------|
| GET | `/health` | Não | Saúde do serviço. |
| POST | `/api/v1/auth/token` | Não (body com client_id/secret) | Retorna JWT. |
| POST/GET/PATCH | `/api/v1/companies` | Bearer JWT | CRUD empresas. |
| POST | `/api/v1/companies/{id}/phone-numbers` | Bearer JWT | Cria número + gera webhook. |
| GET | `/api/v1/companies/{id}/phone-numbers` | Bearer JWT | Lista números. |
| POST | `.../webhook/regenerate` | Bearer JWT | Novo token de webhook. |
| POST/GET/… | `/api/v1/webhooks/whatsapp/{company_id}/{phone_number_id}/{token}` | Token na URL | Recebimento Uazapi (público). |

Formato da URL de webhook (documentação funcional):

`{URL_PUBLICA_DA_API}/api/v1/webhooks/whatsapp/{company_id}/{phone_number_id}/{token}`

Onde `URL_PUBLICA_DA_API` na Render é a do **Web Service** (a mesma base usada em `resolved_public_base_url()`).

---

## 8. Fluxo de deploy (ordem recomendada)

1. Código no GitHub (`main` atualizado).  
2. Na Render: criar Blueprint a partir de [`render.yaml`](render.yaml) **ou** criar serviços manualmente espelhando o arquivo.  
3. **Subir / obter URL** da **API** (Web Service).  
4. No **Static Site**: definir `VITE_API_URL` = URL https da API → **novo deploy** do Static Site (obrigatório após mudar essa variável).  
5. Na **API**: definir `CORS_ORIGINS` = URL https do Static Site.  
6. Na **API**: conferir `AUTH_CLIENT_ID` e `AUTH_CLIENT_SECRET` e usar os mesmos no login do site.  
7. **Uazapi.dev:** configurar webhook com a URL completa gerada pela API (sempre apontando para a **API**, não para o site).

---

## 9. Comandos úteis (máquina local)

```bash
# Backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
# Frontend
cd frontend
npm install
cp .env.example .env   # ajuste VITE_API_URL
npm run dev
```

```bash
# Testes backend
python -m pytest tests/ -v
```

---

## 10. Histórico de commits relevantes (referência)

- **API inicial** — FastAPI, modelos, webhook, Alembic, pytest.  
- **Frontend + CORS + `render.yaml` + `RENDER_EXTERNAL_URL`** — painel React, blueprint Render, documentação de deploy.  
- **Ajustes de login** — mensagens quando `VITE_API_URL`/CORS estão incorretos; README com troubleshooting.

Para a lista exata de commits: `git log --oneline` no repositório local.

---

## 11. Segurança (lembretes)

- **Não** commite `.env` com segredos.  
- **Token do webhook** na URL é sensível; no banco só existe **hash**.  
- **Credencial da instância Uazapi** (`uazapi_instance_token`) hoje é armazenada em texto no banco — em produção forte, usar cofre ou criptografia.  
- **Plano gratuito** da Render: serviço pode **hibernar**; primeira requisição pode demorar.

---

## 12. Deploy na Render: “No open ports” / “Timed Out”

A plataforma verifica se o processo **escuta** em `0.0.0.0:$PORT` e se o **health check** retorna **200**.

- O **start command** correto é: `uvicorn app.main:app --host 0.0.0.0 --port $PORT` (já no [`render.yaml`](render.yaml)).
- Se o health check do painel apontar para **`/`** e a API não tiver rota na raiz, a resposta era **404** e o deploy podia falhar. Por isso existe **`GET /`** em [`app/main.py`](app/main.py) com **200** e o blueprint usa `healthCheckPath: /`.
- O arquivo [`runtime.txt`](runtime.txt) fixa **Python 3.12.x** no build na Render (evita surpresas com versões muito novas, ex. 3.14).

No painel do Web Service, confira **Health Check Path**: use **`/`** ou **`/health`** (ambos respondem OK).

---

## 13. Onde tirar dúvida rápida

| Dúvida | Onde olhar |
|--------|------------|
| Variáveis de exemplo | [`.env.example`](.env.example), [`frontend/.env.example`](frontend/.env.example) |
| Blueprint Render | [`render.yaml`](render.yaml) |
| Login quebrado na internet | Seção “Login no site…” no [`README.md`](README.md) |
| Especificação de produto | [`PROMPT-ARQUITETURA.md`](PROMPT-ARQUITETURA.md) |

---

*Documento gerado para o projeto **webhook** (`farollapi-cloud/webhook`). Atualize os placeholders de URL da Render quando o seu deploy mudar.*
