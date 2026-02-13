# 📌 MVP -- Login com Google + Controle de Acesso (App Desktop Python)

## 🎯 Objetivo

Implementar login com Google em um aplicativo desktop Python, permitindo
que apenas usuários previamente autorizados utilizem o sistema.

------------------------------------------------------------------------

# 🏗️ Arquitetura do MVP

    [ App Desktop Python ]
            ↓
    [ API FastAPI ]
            ↓
    [ Banco de Dados PostgreSQL ]
            ↓
    [ Google OAuth 2.0 ]

------------------------------------------------------------------------

# 🔐 Fluxo de Autenticação

1.  Usuário clica em **"Login com Google"** no app.
2.  O app abre o navegador padrão.
3.  Usuário autentica no Google.
4.  Google redireciona para a API.
5.  API valida o token e extrai o email.
6.  API verifica se o email está autorizado no banco.
7.  Se autorizado:
    -   API gera JWT próprio do sistema.
    -   Retorna token ao app.
8.  App libera acesso.

------------------------------------------------------------------------

# 🧱 Componentes do MVP

## 1️⃣ Backend (FastAPI)

### Dependências

``` bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-jose requests
```

------------------------------------------------------------------------

## 2️⃣ Banco de Dados

### Tabela: users

``` sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

------------------------------------------------------------------------

## 3️⃣ Regras de Negócio

### Autorização

-   Usuário só acessa se:
    -   Existir no banco
    -   is_active = true

### Admin

-   Seu email será inserido manualmente:
    -   role = 'admin'
    -   is_active = true

------------------------------------------------------------------------

# 🔐 Endpoints Necessários

## 🔹 GET /login/google

Redireciona usuário para autenticação do Google.

------------------------------------------------------------------------

## 🔹 GET /auth/callback

Responsável por:

-   Receber `code`
-   Trocar por access_token
-   Validar token
-   Extrair email
-   Verificar autorização
-   Gerar JWT do sistema

------------------------------------------------------------------------

## 🔹 GET /me

Retorna dados do usuário autenticado.

------------------------------------------------------------------------

## 🔹 POST /admin/activate-user

Permite que admin ative usuários.

Proteção: - Só usuários com `role = admin` podem acessar.

------------------------------------------------------------------------

# 🖥️ Integração com o Desktop

## Botão de Login

``` python
import webbrowser

webbrowser.open("https://suaapi.com/login/google")
```

------------------------------------------------------------------------

## Após Login

O app deve:

-   Receber o JWT
-   Salvar localmente (arquivo seguro)
-   Enviar JWT em todas requisições:

``` python
headers = {
    "Authorization": f"Bearer {token}"
}
```

------------------------------------------------------------------------

# 🔑 JWT do Sistema

Payload mínimo:

``` json
{
  "sub": "email@usuario.com",
  "role": "user",
  "exp": 1234567890
}
```

Validade recomendada: - 24 horas

------------------------------------------------------------------------

# 🛡️ Segurança Mínima do MVP

-   Backend obrigatoriamente com HTTPS
-   Tokens com expiração
-   Validação do token em todas rotas protegidas
-   Nunca confiar apenas no frontend

------------------------------------------------------------------------

# 🚀 Deploy do Backend

Opções simples para MVP:

-   VPS básica
-   Render
-   Railway
-   DigitalOcean

Requisitos: - Domínio configurado - HTTPS ativo

------------------------------------------------------------------------

# 📅 Cronograma Simplificado (10 dias)

### Dia 1--2

Criar projeto no Google Cloud e gerar credenciais OAuth.

### Dia 3--4

Configurar FastAPI + Banco de Dados.

### Dia 5--6

Implementar fluxo OAuth completo.

### Dia 7

Implementar JWT próprio.

### Dia 8

Implementar sistema básico de autorização (is_active).

### Dia 9

Integrar desktop com backend.

### Dia 10

Testes com usuários externos.

------------------------------------------------------------------------

# 🎯 Escopo do MVP

Inclui:

-   Login com Google
-   Controle de acesso por email
-   Admin manual
-   Bloqueio remoto
-   JWT próprio

Não inclui (por enquanto):

-   Refresh token
-   Painel administrativo web completo
-   Logs avançados
-   Recuperação de conta
-   Multi-admin

------------------------------------------------------------------------

# 📌 Próximos Passos Após MVP

-   Criar painel web administrativo
-   Implementar refresh tokens
-   Adicionar logs de acesso
-   Criar plano de licenciamento
-   Adicionar métricas de uso

------------------------------------------------------------------------

# ✅ Resultado Esperado

Ao final do MVP você terá:

-   App desktop com login profissional
-   Controle remoto de usuários
-   Base sólida para escalar
-   Estrutura pronta para comercialização futura
