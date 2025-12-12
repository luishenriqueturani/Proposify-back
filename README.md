# Proposify Backend

API REST para plataforma de Marketplace de Serviços utilizando Django Rest Framework.

## 📋 Sobre o Projeto

Proposify é uma plataforma que conecta clientes que precisam de serviços com prestadores que oferecem esses serviços. O projeto é uma API REST pura, sem views/telas, com comunicação via endpoints REST e WebSocket.

### Funcionalidades Principais

- ✅ Sistema de autenticação JWT
- ✅ Gerenciamento de usuários (clientes e prestadores)
- ✅ Categorias e serviços
- ✅ Pedidos de serviço e propostas
- ✅ Sistema de chat em tempo real (WebSocket)
- ✅ Sistema de assinaturas (planos, pagamentos)
- ✅ Pagamentos de serviços
- ✅ Sistema de avaliações/reviews
- ✅ Sistema administrativo
- ✅ Notificações (email e push - preparado para Firebase)
- ✅ Soft Delete (exclusão lógica)
- ✅ Jobs assíncronos (Celery + Redis)

## 🚀 Tecnologias

- **Django 5.2.8** - Framework web
- **Django REST Framework** - API REST
- **PostgreSQL** - Banco de dados
- **Redis** - Cache e message broker
- **Celery** - Tarefas assíncronas
- **Django Channels** - WebSocket
- **JWT** - Autenticação
- **Sentry** - Monitoramento de erros
- **drf-spectacular** - Documentação Swagger/OpenAPI

## 📁 Estrutura do Projeto

```
Proposify-back/
├── api/                          # Apps da API
│   ├── accounts/                 # Usuários, perfis, autenticação
│   ├── services/                 # Categorias e serviços
│   ├── orders/                   # Pedidos e propostas
│   ├── chat/                     # Mensagens entre usuários
│   ├── subscriptions/            # Planos e assinaturas
│   ├── payments/                 # Pagamentos de serviços
│   ├── reviews/                  # Avaliações
│   ├── admin/                    # Gerenciamento administrativo
│   ├── notifications/            # Jobs de email e notificações
│   └── utils/                    # Helpers, mixins, managers (soft delete)
│
├── config/                       # Configurações do projeto
│   ├── settings/
│   │   ├── base.py              # Configurações comuns
│   │   ├── dev.py               # Configurações de desenvolvimento
│   │   └── prod.py              # Configurações de produção
│   └── urls.py                  # URLs principais
│
├── marketplace/                  # Configurações do projeto Django
│   ├── asgi.py                  # Configuração ASGI (WebSocket)
│   ├── wsgi.py                  # Configuração WSGI
│   └── urls.py                  # (legado, usar config/urls.py)
│
├── docs/                         # Documentação
│   ├── proposta.md              # Proposta completa do projeto
│   └── postgres_setup.md        # Instruções de setup do PostgreSQL
│
├── logs/                         # Logs da aplicação
│   ├── django.log               # Logs gerais (JSON)
│   └── django-error.log         # Logs de erros (JSON)
│
├── venv/                         # Ambiente virtual Python
├── manage.py                     # Script de gerenciamento Django
├── requirements.txt              # Dependências de produção
├── requirements-dev.txt          # Dependências de desenvolvimento
├── .env.example                  # Exemplo de variáveis de ambiente
├── .flake8                       # Configuração do Flake8
├── pyproject.toml                # Configurações de ferramentas (mypy, black, isort)
├── pyrightconfig.json            # Configuração do Pyright
└── README.md                     # Este arquivo
```

## 🛠️ Instalação e Setup

### Pré-requisitos

- Python 3.14+
- PostgreSQL 12+
- Redis 5.0+
- Git

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd Proposify-back
```

### 2. Crie e ative o ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 4. Configure o banco de dados PostgreSQL

Siga as instruções em `docs/postgres_setup.md` para criar o banco de dados e usuário.

Resumo rápido:
```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE proposify_db;
CREATE USER proposify_user WITH PASSWORD 'sua_senha_aqui';
GRANT ALL PRIVILEGES ON DATABASE proposify_db TO proposify_user;
\c proposify_db
GRANT ALL ON SCHEMA public TO proposify_user;
GRANT CREATE ON SCHEMA public TO proposify_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO proposify_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO proposify_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO proposify_user;
```

### 5. Configure as variáveis de ambiente

Copie o arquivo `.env.example` para `.env` e configure as variáveis:

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas configurações (veja seção de Variáveis de Ambiente abaixo).

### 6. Execute as migrações

```bash
python manage.py migrate
```

### 7. Crie um superusuário (opcional)

```bash
python manage.py createsuperuser
```

### 8. Execute o servidor de desenvolvimento

```bash
python manage.py runserver
```

A API estará disponível em `http://localhost:8000/`

## 🔧 Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto baseado no `.env.example`. As principais variáveis são:

### Django Settings

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Database (PostgreSQL)

```env
DB_NAME=proposify_db
DB_USER=proposify_user
DB_PASSWORD=sua_senha_aqui
DB_HOST=localhost
DB_PORT=5432
```

### Redis

```env
REDIS_URL=redis://localhost:6379/0
```

### Celery

```env
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TASK_ALWAYS_EAGER=True  # True em dev (executa tarefas sincronamente)
```

### JWT Settings

```env
JWT_ACCESS_TOKEN_LIFETIME=15  # minutos
JWT_REFRESH_TOKEN_LIFETIME=7  # dias
```

### Email Settings

```env
EMAIL_BACKEND=anymail.backends.mailgun.EmailBackend
MAILGUN_API_KEY=your-mailgun-api-key
MAILGUN_SENDER_DOMAIN=your-domain.com
DEFAULT_FROM_EMAIL=noreply@your-domain.com
```

### Sentry (Error Monitoring)

```env
SENTRY_DSN=your-sentry-dsn-here
SENTRY_ENVIRONMENT=development
```

### Firebase Cloud Messaging (futuro)

```env
FCM_SERVER_KEY=your-fcm-server-key
```

### CORS Settings

```env
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
CORS_ALLOW_ALL_ORIGINS=True  # True em desenvolvimento
```

### Media e Static Files

```env
MEDIA_ROOT=/path/to/media
MEDIA_URL=/media/
STATIC_ROOT=/path/to/static
STATIC_URL=/static/
```

## 📚 Documentação da API

A documentação interativa da API está disponível em:

- **Swagger UI**: `http://localhost:8000/api/swagger/`
- **ReDoc**: `http://localhost:8000/api/redoc/`
- **OpenAPI Schema (JSON)**: `http://localhost:8000/api/schema/`

## 🏥 Health Checks

Endpoints para verificar o status do sistema:

- `GET /health/` - Status básico da aplicação
- `GET /health/db/` - Status da conexão com banco de dados
- `GET /health/redis/` - Status da conexão com Redis
- `GET /health/celery/` - Status dos workers Celery

## 🧪 Testes

Execute os testes com:

```bash
# Todos os testes
python manage.py test

# Testes de um app específico
python manage.py test api.utils

# Com cobertura (se pytest-cov estiver instalado)
pytest --cov=api
```

## 🔄 Celery

Para executar tarefas assíncronas, inicie o worker do Celery:

```bash
celery -A marketplace worker -l info
```

Para monitorar o Celery (Flower):

```bash
celery -A marketplace flower
```

## 📝 Logging

Os logs são salvos em:

- `logs/django.log` - Logs gerais (formato JSON estruturado)
- `logs/django-error.log` - Logs de erros (formato JSON estruturado)

Os logs no console usam formato texto legível.

## 🔐 Segurança

- **Senhas**: Sempre usando bcrypt para hash
- **JWT**: Tokens com expiração curta (15 min) e renovação automática
- **CORS**: Configurado adequadamente
- **HTTPS**: Obrigatório em produção
- **Soft Delete**: Implementado para manter integridade referencial

## 📖 Documentação Adicional

- `docs/proposta.md` - Proposta completa do projeto com todos os detalhes
- `docs/postgres_setup.md` - Instruções detalhadas de setup do PostgreSQL
- `todo.md` - Lista de tarefas do projeto

## 🤝 Contribuindo

1. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
2. Commit suas mudanças (`git commit -m 'feat: adiciona nova feature'`)
3. Push para a branch (`git push origin feature/nova-feature`)
4. Abra um Pull Request

## 📄 Licença

Veja o arquivo `LICENSE` para mais detalhes.

## 👥 Autores

- Seu Nome - [seu-email@exemplo.com]

## 🙏 Agradecimentos

- Django e Django REST Framework
- Comunidade open source
