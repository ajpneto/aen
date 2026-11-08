# AENTECH — Gestão de Assistência Técnica, OS & RESTful API

Sistema integrado para gestão de Ordens de Serviço (OS), autenticação segura com JWT, banco de dados SQLite/PostgreSQL com SQLAlchemy, notificações por e-mail via SMTP Gmail, painel administrativo e consulta pública para clientes.

Compatível com **PythonAnywhere** (`https://aen.pythonanywhere.com`), **GitHub Pages** (`https://fazhoje.com/aentech`) e ambiente local (`http://localhost:5000`).

---

### 📦 O que foi implementado e unificado

#### 1. Backend Flask & RESTful API Unificada (`app.py`)
• **Autenticação e Autorização com JWT (HS256 via PyJWT)**:
  - Modelo `Usuario` no banco de dados (`username`, `email`, `senha_hash`, `admin`, `data_criacao`).
  - Hashing com SHA-256 (`username + senha`) e validação via `hmac.compare_digest` (com fallback seguro).
  - Decorators `@login_obrigatorio` e `@admin_obrigatorio` com extração automática de cabeçalho `Authorization: Bearer <token>`.
  - Tratamento nativo para requisições preflight `OPTIONS` de CORS sem bloqueios indesejados.
  - Bootstrap automático do usuário administrador inicial caso a tabela esteja vazia (`ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_EMAIL` do `.env`).

• **Endpoints de Autenticação e Usuários**:
  - `POST /api/login`: Autentica com `username` e `senha`, retornando token JWT e perfil do usuário.
  - `POST /api/logout`: Logout no cliente.
  - `GET /api/me`: Retorna os dados do usuário conectado (validação de sessão).
  - `GET /api/usuarios`: Lista todos os usuários cadastrados (restrito a administradores).
  - `POST /api/usuarios`: Cadastro de novo usuário técnico/admin (restrito a administradores).
  - `DELETE /api/usuarios/<id>`: Exclusão de usuário (com proteção contra auto-exclusão).

• **Endpoint Público de Rastreio (`/api/consulta`)**:
  - Consulta pública e segura por ID, número de OS (`os_numero`) ou telefone do cliente.
  - Retorna apenas dados públicos necessários para acompanhamento do cliente (`to_public_dict`), protegendo senhas/padrões de desbloqueio e dados de contato sensíveis.

• **Gestão de Ordens de Serviço (`OrdemServico`)**:
  - `GET /api/stats`: KPIs e faturamento estimado em tempo real para o dashboard admin (protegido por JWT).
  - `GET /api/os`: Listagem com filtros por status e busca textual ampla (protegido por JWT).
  - `POST /api/os`: Criação de OS com numeração sequencial automática (`OS-2026-XXXX`).
  - `GET /api/os/<id>` e `GET /api/os/numero/<os_numero>`: Detalhes completos da OS para técnicos.
  - `PUT /api/os/<id>`: Atualização de status, laudo técnico, valores e dados do aparelho.
  - `POST /api/os/<id>/aprovar`: Ação expressa em 1 clique que aprova o orçamento e dispara o e-mail de notificação.
  - `POST /api/os/<id>/notificar`: Reenvio manual do e-mail de notificação SMTP.
  - `DELETE /api/os/<id>`: Exclusão segura de OS.

• **Serviço de Arquivos Frontend no Flask**:
  - Rotas amigáveis `/`, `/admin`, `/ordem-de-servico`, `/consultar-os`, `/os` servindo as páginas HTML tanto em desenvolvimento local quanto no PythonAnywhere.

#### 2. Configuração Unificada de Ambiente (`.env` e `.env.example`)
• Todas as variáveis necessárias centralizadas e organizadas por módulos:
  - **Segurança**: `SECRET_KEY`, `JWT_EXPIRES_SECONDS`.
  - **Bootstrap Admin**: `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_EMAIL`.
  - **Banco de Dados**: `DATABASE_URL` (SQLite local ou PostgreSQL remoto).
  - **Empresa / Atendimento**: `BUSINESS_NAME`, `BUSINESS_SLOGAN`, `BUSINESS_CITY`, `BUSINESS_ADDRESS`, `BUSINESS_EMAIL`, `BUSINESS_PHONE`, `WHATSAPP_NUMBER`, `WHATSAPP_LINK`, `BUSINESS_HORARIO`, `BUSINESS_GARANTIA_DIAS`.
  - **Notificações SMTP (Gmail TLS)**: `MAIL_ENABLED`, `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER` (compatível também com chaves `SMTP_*`).
• Arquivo `.env.example` versionado como template para novos ambientes e deploys.

#### 3. Frontend Atualizado com Suporte Completo à Autenticação (`../fazhoje/aentech/` e raiz de `aen`)
• **`admin.html`**:
  - Overlay de login elegante exigindo credenciais antes de exibir dados restritos.
  - Botão de configuração da API REST acessível diretamente da tela de login.
  - Armazenamento seguro de token JWT no `localStorage` (`AENTECH_AUTH_TOKEN`, `AENTECH_AUTH_USER`).
  - Injeção automática de `Authorization: Bearer <token>` em todas as requisições (`authFetch`).
  - Tratamento inteligente de sessão expirada (401).
  - Exibição do usuário conectado na barra de navegação (`@ajpneto`) e botão de logout.
• **`ordem-de-servico.html`**:
  - Permite a técnicos autenticados criar e salvar Ordens de Serviço diretamente no banco de dados.
  - Overlay de login sob demanda com botão de fechamento para visualização e impressão pública.
  - Fallback público para carregamento de OS via `/api/consulta?id=...` ou `?os=...` com impressão A4 automática (`?print=1`).
• **`consultar-os.html`**:
  - Rastreamento público em tempo real sem necessidade de autenticação via `/api/consulta`.
  - Linha do tempo visual em 5 etapas e botão direto para WhatsApp de suporte.
• **`index.html`**:
  - Link de login administrativo adicionado à barra de navegação superior.

---

### 🧪 Testes Automatizados Executados
Todos os fluxos foram testados e validados no ambiente:
1. Conexão ao SQLite e criação de tabelas: ✅
2. Bootstrap automático do usuário administrador inicial: ✅
3. Login com validação de senha e geração de token JWT assinado: ✅
4. Proteção de rotas restritas contra acessos sem token (401 Unauthorized): ✅
5. Validação de token com `/api/me` e `/api/stats`: ✅
6. Criação de nova OS com numeração sequencial automática: ✅
7. Consulta pública desautenticada protegendo senhas e dados confidenciais: ✅
8. Aprovação expressa de orçamento com disparo de e-mail SMTP via TLS Gmail: ✅
9. Listagem, busca e exclusão de OS: ✅
10. Servimento de rotas frontend pelo Flask (`/`, `/admin`, `/ordem-de-servico`, `/consultar-os`): ✅

---

### 🚀 Instruções para Deploy

#### 1. No PythonAnywhere (`https://aen.pythonanywhere.com`):
1. No console do PythonAnywhere, puxe as alterações ou envie os arquivos atualizados:
   - `app.py`
   - `.env`
   - `requirements.txt`
   - `admin.html`, `ordem-de-servico.html`, `consultar-os.html`
2. Instale/atualize as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. No painel Web do PythonAnywhere, clique no botão **Reload**.

#### 2. No GitHub Pages (`https://fazhoje.com/aentech`):
1. No repositório `fazhoje`:
   ```bash
   cd ../fazhoje
   git add aentech/
   git commit -m "feat(aentech): suporte a autenticacao JWT, login admin e consulta publica segura"
   git push origin main
   ```
2. O frontend já está configurado para consumir automaticamente a API em `https://aen.pythonanywhere.com`.

---

agy --conversation=ec963055-4993-4c2f-9fbd-27fc78e08fe4
