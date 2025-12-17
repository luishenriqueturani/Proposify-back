# Enums e Choices do Sistema

Este documento descreve todos os enums e choices utilizados no sistema Proposify.

## 📋 Índice

1. [UserType](#usertype)
2. [OrderStatus](#orderstatus)
3. [ProposalStatus](#proposalstatus)
4. [MessageType](#messagetype)
5. [SubscriptionStatus](#subscriptionstatus)
6. [PaymentStatus](#paymentstatus)
7. [DeviceType](#devicetype)

---

## UserType

**Localização**: `api.accounts.enums.UserType`

**Descrição**: Define os tipos de usuário no sistema.

**Valores**:
- `CLIENT` - Cliente (padrão)
- `PROVIDER` - Prestador de serviços
- `ADMIN` - Administrador

**Uso**:
```python
from api.accounts.enums import UserType

# Obter valor
user_type = UserType.CLIENT.value  # 'CLIENT'

# Obter label
label = UserType.CLIENT.label  # 'Cliente'

# Obter choices para Django
choices = UserType.choices()  # [('CLIENT', 'Cliente'), ...]
```

---

## OrderStatus

**Localização**: `api.orders.enums.OrderStatus`

**Descrição**: Define os status possíveis de um pedido.

**Valores**:
- `PENDING` - Pendente (aguardando propostas)
- `ACCEPTED` - Aceito (proposta aceita)
- `IN_PROGRESS` - Em progresso (serviço sendo executado)
- `COMPLETED` - Completo (serviço finalizado)
- `CANCELLED` - Cancelado

**Fluxo típico**:
```
PENDING → ACCEPTED → IN_PROGRESS → COMPLETED
         ↓
      CANCELLED (pode ocorrer em qualquer momento)
```

**Uso**:
```python
from api.orders.enums import OrderStatus

order.status = OrderStatus.ACCEPTED.value
```

---

## ProposalStatus

**Localização**: `api.orders.enums.ProposalStatus`

**Descrição**: Define os status possíveis de uma proposta.

**Valores**:
- `PENDING` - Pendente (aguardando resposta do cliente)
- `ACCEPTED` - Aceita (cliente aceitou a proposta)
- `DECLINED` - Recusada (cliente recusou a proposta)
- `EXPIRED` - Expirada (prazo de validade expirou)

**Fluxo típico**:
```
PENDING → ACCEPTED (cliente aceita)
       → DECLINED (cliente recusa)
       → EXPIRED (tempo expirou)
```

**Uso**:
```python
from api.orders.enums import ProposalStatus

proposal.status = ProposalStatus.ACCEPTED.value
```

---

## MessageType

**Localização**: `api.chat.enums.MessageType`

**Descrição**: Define os tipos de mensagem no chat.

**Valores**:
- `TEXT` - Mensagem de texto (padrão)
- `IMAGE` - Mensagem com imagem
- `FILE` - Mensagem com arquivo
- `SYSTEM` - Mensagem do sistema

**Uso**:
```python
from api.chat.enums import MessageType

message.message_type = MessageType.IMAGE.value
```

---

## SubscriptionStatus

**Localização**: `api.subscriptions.enums.SubscriptionStatus`

**Descrição**: Define os status possíveis de uma assinatura.

**Valores**:
- `ACTIVE` - Ativa (assinatura ativa e válida)
- `CANCELLED` - Cancelada (assinatura cancelada pelo usuário)
- `EXPIRED` - Expirada (assinatura expirou)
- `SUSPENDED` - Suspensa (assinatura suspensa pela plataforma)

**Uso**:
```python
from api.subscriptions.enums import SubscriptionStatus

subscription.status = SubscriptionStatus.ACTIVE.value
```

---

## PaymentStatus

**Localização**: `api.subscriptions.enums.PaymentStatus`

**Descrição**: Define os status possíveis de um pagamento (usado tanto para pagamentos de serviços quanto de assinaturas).

**Valores**:
- `PENDING` - Pendente (aguardando pagamento)
- `PAID` - Pago (pagamento confirmado)
- `FAILED` - Falhou (pagamento falhou)
- `REFUNDED` - Reembolsado (pagamento foi reembolsado)

**Fluxo típico**:
```
PENDING → PAID (pagamento confirmado)
       → FAILED (pagamento falhou)
       → REFUNDED (após PAID, se reembolsado)
```

**Uso**:
```python
from api.subscriptions.enums import PaymentStatus

payment.payment_status = PaymentStatus.PAID.value
```

---

## DeviceType

**Localização**: `api.notifications.enums.DeviceType`

**Descrição**: Define os tipos de dispositivos para notificações push.

**Valores**:
- `IOS` - Dispositivo iOS (iPhone, iPad)
- `ANDROID` - Dispositivo Android
- `WEB` - Navegador web (PWA)

**Uso**:
```python
from api.notifications.enums import DeviceType

device.device_type = DeviceType.ANDROID.value
```

---

## 📝 Notas Importantes

1. **Todos os enums herdam de `str, Enum`**: Isso permite usar os valores diretamente como strings no Django.

2. **Método `choices()`**: Todos os enums implementam o método `choices()` que retorna tuplas `(value, label)` para uso em campos Django.

3. **Propriedade `label`**: Todos os enums têm uma propriedade `label` que retorna o nome legível em português.

4. **Valores são constantes**: Os valores dos enums são constantes e não devem ser alterados após a criação do banco de dados.

5. **Uso em Models**: Os enums são usados nos campos `choices` dos modelos Django:
   ```python
   status = models.CharField(
       max_length=20,
       choices=OrderStatus.choices(),
       default=OrderStatus.PENDING.value
   )
   ```

