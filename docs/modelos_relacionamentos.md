# Relacionamentos entre Modelos

Este documento descreve todos os relacionamentos entre os modelos do sistema Proposify.

## 📊 Diagrama de Relacionamentos

### 1. Modelos de Conta (Accounts)

#### User
- **OneToOne** → `ProviderProfile` (opcional)
- **OneToOne** → `ClientProfile` (opcional)
- **OneToMany** → `UserSubscription` (histórico de assinaturas)
- **OneToMany** → `Order` (através de `ClientProfile`)
- **OneToMany** → `Proposal` (através de `ProviderProfile`)
- **OneToMany** → `Review` (como `reviewer` e `reviewed_user`)
- **OneToMany** → `ChatRoom` (como `client` e `provider`)
- **OneToMany** → `Message` (como `sender`)
- **OneToMany** → `DeviceToken` (tokens FCM)
- **OneToMany** → `AdminAction` (se for admin)

#### ProviderProfile
- **OneToOne** → `User` (obrigatório)
- **OneToMany** → `Proposal` (propostas feitas pelo prestador)

#### ClientProfile
- **OneToOne** → `User` (obrigatório)
- **OneToMany** → `Order` (pedidos feitos pelo cliente)

### 2. Modelos de Serviços (Services)

#### ServiceCategory
- **ManyToOne (self)** → `ServiceCategory` (parent - para subcategorias)
- **OneToMany** → `ServiceCategory` (children - subcategorias)
- **OneToMany** → `Service` (serviços nesta categoria)

#### Service
- **ManyToOne** → `ServiceCategory` (categoria do serviço)
- **OneToMany** → `Order` (pedidos para este serviço)

### 3. Modelos de Pedidos (Orders)

#### Order
- **ManyToOne** → `ClientProfile` (cliente que fez o pedido)
- **ManyToOne** → `Service` (serviço solicitado)
- **OneToMany** → `Proposal` (propostas recebidas)
- **OneToMany** → `Payment` (pagamentos do pedido)
- **OneToMany** → `Review` (avaliações do pedido)
- **OneToMany** → `ChatRoom` (salas de chat relacionadas)

#### Proposal
- **ManyToOne** → `Order` (pedido ao qual a proposta se refere)
- **ManyToOne** → `ProviderProfile` (prestador que fez a proposta)
- **OneToMany** → `Payment` (pagamentos da proposta aceita)

### 4. Modelos de Pagamento (Payments)

#### Payment
- **ManyToOne** → `Order` (pedido relacionado)
- **ManyToOne** → `Proposal` (proposta aceita que gerou o pagamento)

### 5. Modelos de Avaliação (Reviews)

#### Review
- **ManyToOne** → `Order` (pedido avaliado)
- **ManyToOne** → `User` (como `reviewer` - quem avaliou)
- **ManyToOne** → `User` (como `reviewed_user` - quem foi avaliado)
- **Constraint Única**: (`order`, `reviewer`) - cada usuário só pode avaliar uma vez por pedido

### 6. Modelos de Chat (Chat)

#### ChatRoom
- **ManyToOne** → `Order` (pedido relacionado)
- **ManyToOne** → `User` (como `client` - cliente participante)
- **ManyToOne** → `User` (como `provider` - prestador participante)
- **OneToMany** → `Message` (mensagens da sala)
- **Constraint Única**: (`order`, `client`, `provider`) - uma sala por combinação

#### Message
- **ManyToOne** → `ChatRoom` (sala de chat)
- **ManyToOne** → `User` (como `sender` - remetente)

### 7. Modelos de Assinatura (Subscriptions)

#### SubscriptionPlan
- **OneToMany** → `UserSubscription` (assinaturas neste plano)
- **PROTECT delete**: Não pode ser deletado se houver assinaturas ativas

#### UserSubscription
- **ManyToOne** → `User` (usuário com a assinatura)
- **ManyToOne** → `SubscriptionPlan` (plano de assinatura)
- **OneToMany** → `SubscriptionPayment` (pagamentos da assinatura)

#### SubscriptionPayment
- **ManyToOne** → `UserSubscription` (assinatura relacionada)

### 8. Modelos de Notificação (Notifications)

#### DeviceToken
- **ManyToOne** → `User` (usuário dono do token)
- **Unique**: `token` - cada token é único

### 9. Modelos de Admin (Admin)

#### AdminAction
- **ManyToOne** → `User` (admin que executou a ação)

## 🔄 Comportamento de Delete

### Soft Delete (não propaga)
- Quando um objeto é soft deleted (marcado com `deleted_at`), os objetos relacionados **não são deletados**
- Exemplo: Se um `Order` é soft deleted, suas `Proposal`, `Payment`, `Review` e `ChatRoom` permanecem ativas

### Hard Delete (propaga em cascata)
- Quando um objeto é hard deleted (removido fisicamente), os objetos relacionados são deletados conforme o `on_delete`:
  - **CASCADE**: Objetos relacionados são deletados
  - **PROTECT**: Impede a deleção se houver objetos relacionados

### Exemplos de CASCADE
- `User` hard deleted → `ClientProfile`, `ProviderProfile`, `Order`, `Proposal`, `Review`, `ChatRoom`, `Message`, `UserSubscription`, `DeviceToken`, `AdminAction` são deletados
- `Order` hard deleted → `Proposal`, `Payment`, `Review`, `ChatRoom`, `Message` são deletados
- `ChatRoom` hard deleted → `Message` são deletadas

### Exemplos de PROTECT
- `SubscriptionPlan` não pode ser hard deleted se houver `UserSubscription` ativas

## 📝 Notas Importantes

1. **Usuário Duplo**: Um usuário pode ser CLIENT e PROVIDER ao mesmo tempo, tendo ambos `ClientProfile` e `ProviderProfile`

2. **Avaliações Bidirecionais**: Cliente e prestador podem se avaliar mutuamente no mesmo pedido

3. **ChatRoom Único**: Uma sala de chat é criada por combinação única de (`order`, `client`, `provider`)

4. **Review Único**: Cada usuário só pode fazer uma avaliação por pedido (constraint única em `order` + `reviewer`)

5. **Soft Delete Preserva Dados**: Objetos soft deleted mantêm todos os dados e relacionamentos, apenas não aparecem em queries normais

