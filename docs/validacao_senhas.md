# Validação e Hash de Senhas

Este documento descreve o sistema de validação e hashing de senhas do Proposify.

## Visão Geral

O sistema utiliza:
- **BCrypt** como algoritmo de hash principal
- **Validadores Django** para força de senha
- **Validação customizada** no serializer de registro

## Configuração do Hash (BCrypt)

### Settings (`config/settings/base.py`)

```python
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',  # Principal
    'django.contrib.auth.hashers.BCryptPasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
]
```

### Por que BCrypt?

1. **Resistência a ataques de força bruta**: BCrypt é deliberadamente lento
2. **Salt automático**: Cada hash inclui um salt único
3. **Fator de custo ajustável**: Pode ser aumentado conforme hardware evolui
4. **Amplamente testado**: Padrão da indústria há mais de 20 anos

### Dependência

```bash
pip install bcrypt
```

Já incluído em `requirements.txt`.

---

## Validação de Força de Senha

### Validadores Configurados

```python
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
```

### Regras de Validação

| Validador | Regra |
|-----------|-------|
| `UserAttributeSimilarityValidator` | Senha não pode ser similar ao email/nome |
| `MinimumLengthValidator` | Mínimo 8 caracteres |
| `CommonPasswordValidator` | Bloqueia senhas comuns (ex: "password123") |
| `NumericPasswordValidator` | Não pode ser apenas números |

### Validação Customizada no Serializer

```python
# api/accounts/serializers.py

class UserRegisterSerializer(serializers.Serializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text='Mínimo 8 caracteres'
    )
    password_confirm = serializers.CharField(write_only=True)
    
    def validate_password(self, value):
        """Valida força da senha."""
        if len(value) < 8:
            raise serializers.ValidationError(
                'A senha deve ter no mínimo 8 caracteres.'
            )
        
        if not any(c.isupper() for c in value):
            raise serializers.ValidationError(
                'A senha deve conter pelo menos uma letra maiúscula.'
            )
        
        if not any(c.islower() for c in value):
            raise serializers.ValidationError(
                'A senha deve conter pelo menos uma letra minúscula.'
            )
        
        if not any(c.isdigit() for c in value):
            raise serializers.ValidationError(
                'A senha deve conter pelo menos um número.'
            )
        
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'As senhas não coincidem.'
            })
        return attrs
```

---

## Requisitos de Senha

Para ser aceita, uma senha deve:

1. ✅ Ter no mínimo **8 caracteres**
2. ✅ Conter pelo menos **uma letra maiúscula**
3. ✅ Conter pelo menos **uma letra minúscula**
4. ✅ Conter pelo menos **um número**
5. ✅ Não ser uma **senha comum** (ex: "password", "12345678")
6. ✅ Não ser **similar ao email ou nome** do usuário
7. ✅ Não ser **apenas números**

### Exemplos

| Senha | Válida? | Motivo |
|-------|---------|--------|
| `Senha@123` | ✅ | Atende todos os requisitos |
| `MinhaSenhaForte1` | ✅ | Atende todos os requisitos |
| `senha123` | ❌ | Falta letra maiúscula |
| `SENHA123` | ❌ | Falta letra minúscula |
| `SenhaForte` | ❌ | Falta número |
| `Ab1` | ❌ | Menos de 8 caracteres |
| `password` | ❌ | Senha comum |
| `12345678` | ❌ | Apenas números |

---

## Fluxo de Hash

### Criação de Usuário

```python
# O Django automaticamente faz o hash ao usar create_user
user = User.objects.create_user(
    email='user@example.com',
    password='SenhaSegura@123'  # Texto plano aqui
)

# A senha armazenada é o hash
print(user.password)
# bcrypt_sha256$$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.5kQNz...
```

### Verificação de Senha

```python
# Método do modelo User
user.check_password('SenhaSegura@123')  # True
user.check_password('SenhaErrada')      # False

# Usando função do Django
from django.contrib.auth.hashers import check_password
check_password('SenhaSegura@123', user.password)  # True
```

### Alteração de Senha

```python
# Método set_password cria novo hash
user.set_password('NovaSenha@456')
user.save()

# Senha antiga não funciona mais
user.check_password('SenhaSegura@123')  # False
user.check_password('NovaSenha@456')    # True
```

---

## Reset de Senha

### Fluxo

1. **Solicitar reset**: `POST /auth/password/reset/`
   ```json
   {"email": "user@example.com"}
   ```

2. **Sistema gera token** (válido por tempo limitado)

3. **Confirmar reset**: `POST /auth/password/reset/confirm/`
   ```json
   {
     "uid": "MQ",
     "token": "abc123...",
     "new_password": "NovaSenha@123",
     "new_password_confirm": "NovaSenha@123"
   }
   ```

### Segurança do Reset

- Token expira após uso único
- Token expira após tempo configurado
- UID é codificado em base64 (não expõe ID real)
- Resposta genérica mesmo para emails inexistentes (evita enumeração)

---

## Testes

Os testes de hash e validação estão em:
- `api/accounts/tests/test_auth.py` - Classe `PasswordHashingTestCase`

### Testes Implementados

```python
def test_password_is_hashed_on_create(self):
    """Verifica que senha não é armazenada em texto plano."""

def test_bcrypt_hasher_is_used(self):
    """Verifica que BCrypt é o hasher usado."""

def test_password_verification_works(self):
    """Verifica que check_password funciona."""

def test_password_change_rehashes(self):
    """Verifica que mudar senha cria novo hash."""

def test_bcrypt_is_first_in_hashers(self):
    """Verifica que BCrypt é prioridade na config."""
```

---

## Boas Práticas

1. **Nunca armazene senhas em texto plano**
   ```python
   # ❌ Errado
   user.password = 'minhasenha'
   
   # ✅ Correto
   user.set_password('minhasenha')
   ```

2. **Nunca compare senhas diretamente**
   ```python
   # ❌ Errado
   if user.password == 'minhasenha':
   
   # ✅ Correto
   if user.check_password('minhasenha'):
   ```

3. **Sempre valide força no backend**
   - Validação frontend é UX, não segurança
   - Backend deve sempre validar

4. **Use HTTPS em produção**
   - Senhas trafegam em texto plano no corpo da requisição
   - HTTPS criptografa o transporte

5. **Não exponha hash em APIs**
   ```python
   class UserSerializer(serializers.ModelSerializer):
       class Meta:
           model = User
           exclude = ['password']  # Nunca retorne o hash
   ```
