# Configuração do PostgreSQL para o Proposify Backend

## 1. Conectar ao PostgreSQL

### Opção A: Conectar com usuário postgres (padrão)
```bash
sudo -u postgres psql
```

### Opção B: Se você tem um usuário PostgreSQL específico
```bash
psql -U seu_usuario_postgres
```

### Opção C: Conectar diretamente especificando usuário e banco
```bash
psql -U postgres -d postgres
```

## 2. Criar o Banco de Dados

Após conectar, execute no psql:

```sql
-- Criar o banco de dados
CREATE DATABASE proposify_db
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'pt_BR.UTF-8'
    LC_CTYPE = 'pt_BR.UTF-8'
    TEMPLATE = template0;

-- Ou versão mais simples (se não precisar especificar locale)
CREATE DATABASE proposify_db;
```

## 3. Criar o Usuário

```sql
-- Criar usuário com senha
CREATE USER proposify_user WITH PASSWORD 'marketplace_password';

-- Ou criar com mais opções (se necessário)
CREATE USER proposify_user 
    WITH 
    PASSWORD 'marketplace_password'
    CREATEDB
    NOSUPERUSER
    NOCREATEROLE
    INHERIT
    LOGIN
    REPLICATION
    BYPASSRLS;
```

## 4. Dar Permissões ao Usuário

```sql
-- Conceder todas as permissões no banco de dados
GRANT ALL PRIVILEGES ON DATABASE proposify_db TO proposify_user;

-- Conectar ao banco de dados criado
\c proposify_db

-- Conceder permissões no schema público (necessário para migrations)
GRANT ALL ON SCHEMA public TO proposify_user;
GRANT CREATE ON SCHEMA public TO proposify_user;

-- Conceder permissões em todas as tabelas existentes e futuras
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO proposify_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO proposify_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO proposify_user;

-- Se já houver tabelas, conceder permissões explicitamente
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO proposify_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO proposify_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO proposify_user;
```

## 5. Verificar Permissões

```sql
-- Verificar usuários
\du

-- Verificar bancos de dados
\l

-- Verificar permissões do usuário no banco
\dp

-- Verificar conexão do usuário
SELECT current_user, current_database();
```

## 6. Sair do psql

```sql
\q
```

## Script Completo (Tudo de uma vez)

Você pode executar tudo de uma vez criando um arquivo SQL:

```bash
sudo -u postgres psql << EOF
-- Criar banco de dados
CREATE DATABASE proposify_db;

-- Criar usuário
CREATE USER proposify_user WITH PASSWORD 'marketplace_password';

-- Conceder permissões no banco
GRANT ALL PRIVILEGES ON DATABASE proposify_db TO proposify_user;

-- Conectar ao banco
\c proposify_db

-- Conceder permissões no schema
GRANT ALL ON SCHEMA public TO proposify_user;
GRANT CREATE ON SCHEMA public TO proposify_user;

-- Permissões padrão para objetos futuros
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO proposify_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO proposify_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO proposify_user;
EOF
```

## Comandos Úteis Adicionais

### Alterar senha do usuário
```sql
ALTER USER proposify_user WITH PASSWORD 'nova_senha';
```

### Remover usuário (se necessário)
```sql
DROP USER IF EXISTS proposify_user;
```

### Remover banco de dados (se necessário)
```sql
DROP DATABASE IF EXISTS proposify_db;
```

### Conectar diretamente com o usuário criado
```bash
psql -U proposify_user -d proposify_db -h localhost
```

## Notas Importantes

1. **Segurança**: Altere a senha `marketplace_password` para uma senha forte em produção
2. **Host**: Se o PostgreSQL estiver em outro host, adicione `-h hostname` nos comandos
3. **Porta**: Se usar porta diferente da padrão (5432), adicione `-p porta`
4. **pg_hba.conf**: Certifique-se de que o arquivo `pg_hba.conf` permite conexões do tipo necessário (md5, scram-sha-256, etc.)

## Verificar Configuração do pg_hba.conf

```bash
# Localizar o arquivo
sudo find /etc -name pg_hba.conf 2>/dev/null
# ou
sudo find /var/lib -name pg_hba.conf 2>/dev/null

# Ver conteúdo (geralmente em /etc/postgresql/[versão]/main/pg_hba.conf)
sudo cat /etc/postgresql/*/main/pg_hba.conf
```

A linha para permitir conexões locais deve estar assim:
```
local   all             all                                     peer
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
```

