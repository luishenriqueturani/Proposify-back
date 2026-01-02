# Sistema de Permissões

Este documento descreve o sistema de permissões customizadas do Proposify.

## Visão Geral

O sistema utiliza permissões do Django REST Framework para controlar acesso aos endpoints. As permissões são baseadas no tipo de usuário (`UserType`) e em relacionamentos de propriedade.

## Localização

As permissões estão centralizadas em:
- `api/accounts/permissions.py` - Permissões base (tipo de usuário)
- `api/admin/permissions.py` - Re-exporta `IsAdmin` para compatibilidade

## Permissões Disponíveis

### IsClient

**Descrição:** Permite acesso apenas a usuários do tipo CLIENT.

```python
from api.accounts.permissions import IsClient

class MinhaView(APIView):
    permission_classes = [IsAuthenticated, IsClient]
```

**Comportamento:**
- ✅ Usuário com `user_type='CLIENT'` → Permitido
- ❌ Usuário com `user_type='PROVIDER'` → Negado
- ❌ Usuário com `user_type='ADMIN'` → Negado
- ❌ Usuário não autenticado → Negado

**Mensagem de erro:** "Apenas clientes podem acessar este recurso."

---

### IsProvider

**Descrição:** Permite acesso apenas a usuários do tipo PROVIDER.

```python
from api.accounts.permissions import IsProvider

class MinhaView(APIView):
    permission_classes = [IsAuthenticated, IsProvider]
```

**Comportamento:**
- ✅ Usuário com `user_type='PROVIDER'` → Permitido
- ❌ Usuário com `user_type='CLIENT'` → Negado
- ❌ Usuário com `user_type='ADMIN'` → Negado
- ❌ Usuário não autenticado → Negado

**Mensagem de erro:** "Apenas prestadores podem acessar este recurso."

---

### IsAdmin

**Descrição:** Permite acesso a administradores do sistema.

```python
from api.accounts.permissions import IsAdmin
# ou
from api.admin.permissions import IsAdmin  # compatibilidade

class MinhaView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]
```

**Comportamento:**
- ✅ Usuário com `user_type='ADMIN'` → Permitido
- ✅ Usuário com `is_staff=True` → Permitido
- ✅ Usuário com `is_superuser=True` → Permitido
- ❌ Usuário comum (CLIENT ou PROVIDER) → Negado
- ❌ Usuário não autenticado → Negado

**Mensagem de erro:** "Apenas administradores podem acessar este recurso."

---

### IsClientOrProvider

**Descrição:** Permite acesso a clientes OU prestadores (exclui admins).

```python
from api.accounts.permissions import IsClientOrProvider

class MinhaView(APIView):
    permission_classes = [IsAuthenticated, IsClientOrProvider]
```

**Comportamento:**
- ✅ Usuário com `user_type='CLIENT'` → Permitido
- ✅ Usuário com `user_type='PROVIDER'` → Permitido
- ❌ Usuário com `user_type='ADMIN'` → Negado
- ❌ Usuário não autenticado → Negado

**Mensagem de erro:** "Apenas clientes ou prestadores podem acessar este recurso."

**Uso típico:** Endpoints que ambos podem acessar, como chat ou visualização de perfis públicos.

---

### IsOwnerOrAdmin

**Descrição:** Permissão de objeto que verifica se o usuário é o dono do recurso ou um admin.

```python
from api.accounts.permissions import IsOwnerOrAdmin

class MinhaView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
```

**Comportamento:**
- ✅ Admin → Sempre permitido
- ✅ Dono do objeto → Permitido
- ❌ Outro usuário → Negado

**Como identifica o dono:**
1. Verifica atributo `user` no objeto
2. Verifica atributo `client` no objeto
3. Verifica atributo `provider` no objeto
4. Verifica método `get_owner()` no objeto

**Exemplo de modelo compatível:**
```python
class Order(models.Model):
    client = models.ForeignKey(User, ...)  # IsOwnerOrAdmin vai usar este campo
```

---

## Combinando Permissões

### Usando AND (todas devem ser verdadeiras)

```python
# Usuário deve ser autenticado E ser cliente
permission_classes = [IsAuthenticated, IsClient]
```

### Usando OR (pelo menos uma deve ser verdadeira)

```python
from rest_framework.permissions import BasePermission

class IsClientOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return IsClient().has_permission(request, view) or \
               IsAdmin().has_permission(request, view)
```

---

## Permissões em ViewSets

```python
from rest_framework import viewsets
from api.accounts.permissions import IsClient, IsProvider, IsOwnerOrAdmin

class OrderViewSet(viewsets.ModelViewSet):
    
    def get_permissions(self):
        if self.action == 'create':
            # Apenas clientes podem criar pedidos
            return [IsAuthenticated(), IsClient()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Apenas o dono ou admin pode editar/deletar
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        else:
            # Listagem e detalhes: qualquer autenticado
            return [IsAuthenticated()]
```

---

## Permissões por Action (decorator)

```python
from rest_framework.decorators import action
from api.accounts.permissions import IsAdmin

class UserViewSet(viewsets.ModelViewSet):
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def suspend(self, request, pk=None):
        """Apenas admins podem suspender usuários."""
        pass
```

---

## Testando Permissões

```python
from django.test import TestCase
from api.accounts.permissions import IsClient
from api.accounts.models import User
from api.accounts.enums import UserType

class MockRequest:
    def __init__(self, user):
        self.user = user

class IsClientPermissionTest(TestCase):
    def test_client_allowed(self):
        user = User.objects.create_user(
            email='client@test.com',
            password='test123',
            user_type=UserType.CLIENT.value
        )
        permission = IsClient()
        request = MockRequest(user=user)
        
        self.assertTrue(permission.has_permission(request, None))
```

---

## Permissões Futuras (por módulo)

As seguintes permissões serão criadas junto com seus respectivos módulos:

| Permissão | Módulo | Descrição |
|-----------|--------|-----------|
| `IsOrderOwner` | Orders | Verifica se é o cliente do pedido |
| `CanCreateOrder` | Orders | Verifica limites da assinatura |
| `IsProposalOwner` | Proposals | Verifica se é o prestador da proposta |
| `CanCreateProposal` | Proposals | Verifica limites da assinatura |
| `IsChatRoomParticipant` | Chat | Verifica se participa da sala |
| `IsSubscriptionOwner` | Subscriptions | Verifica se é dono da assinatura |
| `HasActiveSubscription` | Subscriptions | Verifica se tem assinatura ativa |

---

## Boas Práticas

1. **Sempre use `IsAuthenticated` junto** com permissões de tipo:
   ```python
   permission_classes = [IsAuthenticated, IsClient]  # ✅ Correto
   permission_classes = [IsClient]  # ⚠️ Funciona, mas menos explícito
   ```

2. **Prefira permissões específicas** ao invés de verificar `user_type` manualmente:
   ```python
   # ✅ Bom
   permission_classes = [IsClient]
   
   # ❌ Evitar
   def has_permission(self, request, view):
       return request.user.user_type == 'CLIENT'
   ```

3. **Use `IsOwnerOrAdmin` para recursos com dono**:
   ```python
   # ✅ Permite admin gerenciar tudo + dono gerenciar seu próprio recurso
   permission_classes = [IsOwnerOrAdmin]
   ```

4. **Documente as permissões no Swagger**:
   ```python
   @extend_schema(
       description="Endpoint restrito a clientes.",
       responses={403: "Apenas clientes podem acessar."}
   )
   ```
