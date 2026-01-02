# Autenticação JWT

Este documento descreve o sistema de autenticação JWT do Proposify.

## Visão Geral

O sistema utiliza **JSON Web Tokens (JWT)** para autenticação stateless via:
- `djangorestframework-simplejwt` para geração e validação de tokens
- Token Blacklist para logout seguro
- Rotação de tokens para segurança adicional

## Configuração

### Settings (`config/settings/base.py`)

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'TOKEN_TYPE_CLAIM': 'token_type',
}
```

### Tempos de Expiração

| Token | Duração | Uso |
|-------|---------|-----|
| Access Token | 30 minutos | Autenticar requisições |
| Refresh Token | 7 dias | Renovar access token |

---

## Endpoints de Autenticação

### Registro

```http
POST /api/auth/register/
Content-Type: application/json

{
  "email": "user@example.com",
  "first_name": "João",
  "last_name": "Silva",
  "password": "SenhaSegura@123",
  "password_confirm": "SenhaSegura@123",
  "user_type": "CLIENT"
}
```

**Resposta (201):**
```json
{
  "message": "Usuário registrado com sucesso.",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "João",
    "last_name": "Silva",
    "user_type": "CLIENT"
  }
}
```

---

### Login

```http
POST /api/auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SenhaSegura@123"
}
```

**Resposta (200):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "João",
    "last_name": "Silva",
    "user_type": "CLIENT"
  }
}
```

---

### Refresh Token

```http
POST /api/auth/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Resposta (200):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

> **Nota:** Com `ROTATE_REFRESH_TOKENS=True`, um novo refresh token é retornado. O anterior é invalidado.

---

### Logout

```http
POST /api/auth/logout/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Resposta (200):**
```json
{
  "message": "Logout realizado com sucesso."
}
```

O refresh token é adicionado à blacklist e não pode mais ser usado.

---

### Dados do Usuário Atual

```http
GET /api/auth/me/
Authorization: Bearer <access_token>
```

**Resposta (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "João",
  "last_name": "Silva",
  "full_name": "João Silva",
  "user_type": "CLIENT",
  "phone": null,
  "has_client_profile": true,
  "has_provider_profile": false,
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

### Atualizar Dados do Usuário

```http
PATCH /api/auth/me/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "first_name": "José",
  "phone": "11999998888"
}
```

---

## Usando Tokens em Requisições

### Header de Autorização

```http
GET /api/algum-endpoint-protegido/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Exemplo com cURL

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SenhaSegura@123"}' \
  | jq -r '.access')

# Usar token
curl -X GET http://localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer $TOKEN"
```

### Exemplo com JavaScript

```javascript
// Login
const loginResponse = await fetch('/api/auth/login/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'SenhaSegura@123'
  })
});
const { access, refresh } = await loginResponse.json();

// Armazenar tokens
localStorage.setItem('accessToken', access);
localStorage.setItem('refreshToken', refresh);

// Usar em requisições
const response = await fetch('/api/auth/me/', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
  }
});
```

---

## Estrutura do Token

### Access Token (decodificado)

```json
{
  "token_type": "access",
  "exp": 1705320600,
  "iat": 1705318800,
  "jti": "abc123def456",
  "user_id": "1"
}
```

| Claim | Descrição |
|-------|-----------|
| `token_type` | Tipo do token ("access" ou "refresh") |
| `exp` | Timestamp de expiração |
| `iat` | Timestamp de criação (issued at) |
| `jti` | ID único do token (para blacklist) |
| `user_id` | ID do usuário |

---

## Fluxo de Renovação de Token

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUXO DE AUTENTICAÇÃO                        │
└─────────────────────────────────────────────────────────────────┘

1. LOGIN
   Client ──POST /auth/login/──> Server
   Client <──access + refresh──  Server

2. REQUISIÇÃO AUTENTICADA
   Client ──GET /api/...──> Server  (Header: Bearer access_token)
   Client <──200 OK──────── Server

3. TOKEN EXPIRADO
   Client ──GET /api/...──> Server  (Header: Bearer access_token_expirado)
   Client <──401 Unauthorized── Server

4. REFRESH
   Client ──POST /auth/refresh/──> Server  (Body: refresh_token)
   Client <──novo access + refresh── Server

5. LOGOUT
   Client ──POST /auth/logout/──> Server  (Body: refresh_token)
   Client <──200 OK──────────────── Server
   (refresh_token adicionado à blacklist)
```

---

## Documentação Swagger

### Configuração do Security Scheme

O Swagger está configurado para suportar autenticação JWT:

```python
# config/settings/base.py
SPECTACULAR_SETTINGS = {
    'SECURITY': [{'bearerAuth': []}],
    'COMPONENTS': {
        'securitySchemes': {
            'bearerAuth': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
            }
        }
    },
}
```

### Usando no Swagger UI

1. Acesse `/api/swagger/`
2. Clique em **Authorize** (cadeado)
3. Cole o token no formato: `Bearer seu_token_aqui`
4. Clique em **Authorize**
5. Agora as requisições incluem o header de autorização

### Testando Endpoints

1. **Faça login** via `POST /api/auth/login/`
2. **Copie o `access` token** da resposta
3. **Clique em Authorize** e cole o token
4. **Teste endpoints protegidos** como `/api/auth/me/`

---

## Tratamento de Erros

### Token Inválido

```json
{
  "detail": "Given token not valid for any token type",
  "code": "token_not_valid",
  "messages": [
    {
      "token_class": "AccessToken",
      "token_type": "access",
      "message": "Token is invalid or expired"
    }
  ]
}
```

### Token Expirado

```json
{
  "detail": "Token is invalid or expired",
  "code": "token_not_valid"
}
```

### Token na Blacklist

```json
{
  "detail": "Token is blacklisted",
  "code": "token_not_valid"
}
```

### Sem Token

```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

## Segurança

### Recomendações

1. **Use HTTPS em produção** - Tokens são sensíveis
2. **Não armazene tokens em cookies sem flags de segurança**
   ```javascript
   // Se usar cookies, configure:
   // HttpOnly, Secure, SameSite=Strict
   ```
3. **Implemente refresh token rotation** (já configurado)
4. **Use tempos de expiração curtos** para access tokens
5. **Invalide tokens no logout** (blacklist configurada)

### Armazenamento no Frontend

| Local | Prós | Contras |
|-------|------|---------|
| `localStorage` | Simples, persiste | Vulnerável a XSS |
| `sessionStorage` | Não persiste entre abas | Vulnerável a XSS |
| `httpOnly Cookie` | Protegido de XSS | Vulnerável a CSRF, mais complexo |
| `Memory` | Mais seguro | Perde no refresh da página |

**Recomendação:** Use `localStorage` para SPAs com boas práticas de XSS, ou cookies httpOnly para maior segurança.

---

## Testes

Os testes de JWT estão em:
- `api/accounts/tests/test_auth.py`

### Classes de Teste

- `JWTTokenGenerationTestCase` - Geração de tokens
- `JWTTokenValidationTestCase` - Validação de tokens
- `JWTTokenRefreshTestCase` - Refresh de tokens
- `JWTTokenBlacklistTestCase` - Blacklist de tokens
- `AuthenticationE2ETestCase` - Fluxos completos

---

## Comandos Úteis

### Gerar Token Manualmente (Django Shell)

```python
from rest_framework_simplejwt.tokens import RefreshToken
from api.accounts.models import User

user = User.objects.get(email='user@example.com')
refresh = RefreshToken.for_user(user)

print(f"Access: {refresh.access_token}")
print(f"Refresh: {refresh}")
```

### Decodificar Token (sem validar)

```python
import jwt

token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
decoded = jwt.decode(token, options={"verify_signature": False})
print(decoded)
```

### Limpar Tokens Expirados

```bash
python manage.py flushexpiredtokens
```
