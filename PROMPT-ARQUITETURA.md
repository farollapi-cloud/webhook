# Prompt oficial — Arquitetura backend SaaS multiempresa (WhatsApp + Uazapi.dev)

Documento-base para orientar desenho e implementação do sistema. Versão revisada com suposições explícitas, segurança e políticas de webhook definidas.

---

## Suposições e não-objetivos

- **Suposições**: API de gestão (empresas/números) é consumida por frontend ou integrações **autenticadas**; o endpoint recebedor de webhook é **público** na URL, protegido por token imprevisível no path (e assinatura do provedor, se existir na documentação da Uazapi.dev).
- **Não-objetivo neste MVP**: processamento de mensagens, CRM, IA, chatbot, relatórios, automações, telas completas.
- **Pós-MVP (fora deste escopo)**: deduplicação avançada, dashboards, múltiplos provedores além de Uazapi, workflows.

---

## PAPEL

Você é um arquiteto de software sênior e engenheiro backend especialista em Python, APIs, multi-tenant e integrações via webhook.

---

## MISSÃO

Projetar do zero um sistema backend SaaS multiempresa com API própria, cujo objetivo inicial é exclusivamente:

1. Cadastrar empresas  
2. Cadastrar números de WhatsApp vinculados a essas empresas  
3. Gerar automaticamente um webhook exclusivo para cada número  
4. Exibir esse webhook para configuração manual no painel da Uazapi.dev  
5. Receber os eventos enviados pela Uazapi.dev nesse webhook  
6. Disponibilizar tudo por API para consumo futuro por frontend ou integrações externas  

---

## CONTEXTO REAL DO PROJETO

- Sistema criado **do zero** — não adaptar legado nem assumir monólito existente.  
- **Não** acoplar CRM, chatbot, IA, monitoramento de grupos, relatórios ou automações complexas.  
- **Não** inventar funcionalidades fora do escopo.  
- Foco: infraestrutura inicial correta de empresas, números, webhook por número, recepção segura dos eventos da Uazapi, API limpa e extensível.

---

## RESULTADO ESPERADO

Solução técnica real, prática, implementável e coerente, servindo como base oficial do projeto. Resposta **não genérica**: arquitetura de produto real.

---

## CENÁRIO FUNCIONAL

### Etapa 1 — Cadastro da empresa

Campos sugeridos: razão social ou nome; nome do responsável; e-mail; telefone; status (enum fechado, ex.: `active`, `inactive`, `suspended`); observações opcionais; data de criação; campos de auditoria (criado/atualizado por, timestamps).

### Etapa 2 — Cadastro do número de WhatsApp

Vinculado à empresa: nome de identificação; número de telefone **normalizado (E.164)**; tipo/conexão: `uazapi` (enum `provider` preparado para futuro); URL/base da instância Uazapi; token/credencial da instância (armazenamento seguro — ver seção Segurança); status da conexão.

### Etapa 3 — Geração automática do webhook

Ao cadastrar o número **pela primeira vez**, o backend gera um webhook exclusivo.

**Formato da URL:**

`{BACKEND_PUBLIC_URL}/api/v1/webhooks/whatsapp/{company_id}/{phone_number_id}/{token}`

Onde:

- `company_id` = UUID ou identificador interno da empresa (não confundir com dados públicos da empresa).  
- `phone_number_id` = **identificador interno do registro** do número no sistema — **não** é o MSISDN em si.  
- `token` = segredo criptograficamente seguro e imprevisível gerado no backend (ex.: `secrets.token_urlsafe` ou equivalente com entropia adequada).

**Transação**: criação do `PhoneNumber` + registro de `WebhookConfig` (ou equivalente) na **mesma transação** para não existir número sem webhook órfão ou webhook sem número.

### Etapa 4 — Exibição do webhook

Após salvar o número, a API devolve a URL completa do webhook para cópia e configuração manual na Uazapi.dev.

### Etapa 5 — Recebimento dos eventos

Quando a Uazapi.dev enviar eventos:

- Resolver `company_id`, `phone_number_id` e validar `token`.  
- Validar pertencimento: número pertence à empresa.  
- Rejeitar se empresa/número/webhook não existirem, token inválido, ou **webhook/número/empresa inativos** (política de desativação explícita abaixo).  
- Persistir payload bruto (event log).  
- Opcionalmente enfileirar processamento assíncrono.  
- Responder **rápido** com HTTP **200** e corpo mínimo acordado (ex.: `{"received": true}`), se a documentação da Uazapi exigir corpo específico, alinhar a ela.

**Política HTTP no endpoint público (definir no desenho):**

- **Recomendado para MVP**: falha de autenticação (token inválido, IDs inexistentes, mismatch empresa↔número) → **401** ou **404** (escolher uma estratégia consistente; **404** uniforme reduz enumeração). Sucesso após validação e persistência mínima → **200**.  
- Evitar **200** em todo caso com corpo de erro sem necessidade — isso mascara problemas e dificulta observabilidade.  
- Documentar: provedores costumam **repetir** envios em não-2xx; por isso o handler deve ser **leve** e idempotência pode ser fase posterior.

**Idempotência (opcional no MVP, explícita no desenho):** se a Uazapi enviar identificador único de evento, persistir e ignorar duplicatas; se não enviar, registrar todos os POSTs e tratar deduplicação como melhoria futura.

**Limites:** tamanho máximo de body; timeout curto no worker; rate limiting por IP ou rota (camada de borda ou middleware).

---

## REGRAS DE NEGÓCIO OBRIGATÓRIAS

### 1. Estabilidade absoluta do webhook

Depois de gerado, o webhook **não pode mudar sozinho**. O que permanece estável é o par **(identificadores na URL + segredo atual válido)** salvo em `WebhookConfig`, exceto na regeneração explícita.

Não alterar token/URL por: leituras (GET); recarga de tela; atualização comum de empresa ou número; login/logout; nova consulta à API.

Reformulação técnica: **nenhuma operação que não seja `regenerate` pode alterar `webhook_secret` (ou hash) nem gerar novo token.**

### 2. Regeneração só por ação explícita

Ex.: `POST /api/v1/phone-numbers/{id}/webhook/regenerate` (autenticado e com escopo na empresa).

Efeitos: invalidar token anterior; gerar novo token; persistir novo estado; retornar nova URL; mensagem clara de que a Uazapi.dev precisa ser atualizada manualmente.

### 3. Segurança obrigatória

- Token: geração com `secrets` (ou equivalente); comparação em tempo constante (`hmac.compare_digest` em Python).  
- Não derivar token de dados previsíveis (empresa, telefone, e-mail).  
- **Se** a Uazapi.dev documentar assinatura HMAC ou header de assinatura: validar após identificar o destino; caso contrário, documentar a limitação (confiança no segredo de URL + HTTPS).  
- Não logar token completo em logs de aplicação.

### 4. Multiempresa

Isolamento estrito: cada consulta e mutação na API de gestão deve estar no contexto da empresa autorizada. Cada número pertence a uma única empresa; cada webhook a um único número.

### 5. Recebedor rápido e resiliente

Validar → persistir evento bruto → enfileirar (se houver fila) → **200** rápido. Sem processamento pesado síncrono.

### 6. Escopo

Não implementar agora: chatbot, CRM, IA, grupos, relatórios, análise de mensagem, automações, frontend completo.

### 7. Webhook e entidades inativas

Definir e documentar precedência, por exemplo:

- Empresa `inactive`/`suspended` → não aceitar eventos (404/401 conforme política).  
- Número inativo → idem.  
- Flag `webhook_enabled` ou `WebhookConfig.active = false` → idem.

---

## O QUE VOCÊ DEVE ENTREGAR

Resposta nos blocos abaixo, **nesta ordem**, técnica e específica.

---

## 1. Visão geral da arquitetura

- Backend (framework Python, camadas).  
- Banco relacional e migrações.  
- **Autenticação da API de gestão** (ex.: JWT + escopo por empresa, ou API keys por tenant — justificar simplicidade vs segurança).  
- Filas (Redis/RabbitMQ/SQS — opcional no MVP mas recomendado para worker).  
- Logs estruturados, correlation id, níveis por ambiente.  
- Organização por módulos (domínios: companies, phone_numbers, webhooks, inbound_events).  
- Escalabilidade: stateless API, fila para trabalhos pesados, leitura/escrita separáveis no futuro.

---

## 2. Modelagem de dados

Entidades mínimas: **Company**, **PhoneNumber**, **WebhookConfig**, **WebhookEventLog**.

Incluir: campos principais, tipos, relacionamentos, auditoria, índices, restrições (unicidade `(company_id, e164)` ou política explícita de duplicata), FKs em cascata conforme regra de negócio.

---

## 3. Regras de criação do webhook

Momento exato da criação; prevenção de duplicação (transação + constraint); estabilidade; regeneração; invalidação do token anterior (marcar revogado ou substituir hash de uma só vez).

---

## 4. Design da API REST

Para cada endpoint: método, rota, finalidade, exemplo de request/response, status codes.

Mínimo:

- CRUD/listagem/detalhe de empresas (criar, editar, listar, detalhar).  
- CRUD de números por empresa + listar por empresa.  
- Consultar URL do webhook do número (GET dedicado ou inclusão no recurso do número — sem regenerar token).  
- Regenerar webhook.  
- POST recebedor do webhook (público).  
- **Autenticação** nos endpoints de gestão (exceto health/openapi se houver).

---

## 5. Fluxo completo de ponta a ponta

Passo a passo: empresa → número → webhook gerado → exibido → configuração Uazapi → POST → validação → 200.

---

## 6. Segurança e validações

Geração de token; armazenamento (hash vs segredo necessário para URL — trade-off: URL completa só no create/regenerate se apenas hash armazenado); comparação segura; enumeração (404 uniforme); inativos; regeneração; variáveis sensíveis da Uazapi (criptografia em repouso ou secret manager em produção).

---

## 7. Variáveis de ambiente

Listar e explicar: `BACKEND_PUBLIC_URL`, `DATABASE_URL`, `REDIS_URL` (se fila/cache), `SECRET_KEY` (assinaturas JWT se aplicável), `ENVIRONMENT`, `LOG_LEVEL`, credenciais de fila, etc.

---

## 8. Critérios de aceite e testes práticos

Testes objetivos: criação empresa/número; webhook na primeira criação; estabilidade após GETs/PUTs; regeneração; token antigo inválido; POST simulado; tempo de resposta; isolamento multiempresa; inativação bloqueando recebimento.

---

## 9. Stack recomendada

Python; framework API (FastAPI sugerido); PostgreSQL; Alembic; Pydantic; fila/worker conforme ambiente; testes (pytest). Justificar simplicidade e manutenção.

---

## 10. Plano de implementação por fases

Sequência lógica (ex.: base do projeto → empresas → números → webhook → recepção → testes e hardening).

---

## REGRAS DE RESPOSTA

- Técnico e específico; sem respostas genéricas.  
- Não misturar CRM, IA ou chatbot.  
- Não propor processamento de mensagens além de persistir e enfileirar.  
- Versionamento: `/api/v1/`; mudanças incompatíveis futuras em `/v2/`.  
- Foco: empresa + número + webhook + recepção de eventos.

---

## Notas de revisão (changelog deste documento)

- Autenticação da API administrativa explicitada.  
- Política HTTP e retry do webhook esclarecida; recomendação contra “200 sempre”.  
- Idempotência mencionada como opcional/evolutiva.  
- `phone_number_id` como ID interno; telefone em E.164.  
- Transação na criação número + webhook.  
- Limites de payload, rate limit e logs sem vazamento de token.  
- Estados inativos e precedência descritos.  
- Validação de assinatura do provedor se existir na documentação Uazapi.
