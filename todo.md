# TODO - Proposify Backend

Lista de tarefas organizadas para desenvolvimento do projeto Marketplace de Serviços.

## 📋 Legenda de Status

- ⬜ **Pendente** - Tarefa ainda não iniciada
- 🔄 **Em Progresso** - Tarefa em desenvolvimento
- ✅ **Concluída** - Tarefa finalizada
- ⏸️ **Pausada** - Tarefa temporariamente pausada
- ❌ **Cancelada** - Tarefa cancelada

---

## 🚀 FASE 1: Setup e Configuração Inicial

### 1.1. Estrutura do Projeto
- ✅ Criar estrutura de pastas base do projeto
- ✅ Configurar `manage.py`
- ⬜ Criar estrutura de apps (accounts, services, orders, chat, subscriptions, payments, reviews, admin, notifications, utils)
- ✅ Configurar `requirements.txt` com dependências básicas
- ✅ Configurar `requirements-dev.txt` com dependências de desenvolvimento
- ⬜ Criar arquivo `.env.example`
- ✅ Configurar `.gitignore`
- ✅ Criar ambiente virtual (venv)
- ✅ Instalar dependências do projeto

### 1.2. Configuração Django
- ⬜ Configurar `config/settings/base.py`
- ⬜ Configurar `config/settings/dev.py`
- ⬜ Configurar `config/settings/prod.py`
- ⬜ Configurar `config/urls.py`
- ⬜ Configurar variáveis de ambiente
- ⬜ Configurar conexão com PostgreSQL

### 1.3. Soft Delete (Base)
- ⬜ Criar `api/utils/managers.py` com `SoftDeleteManager`
- ⬜ Criar `api/utils/models.py` com `SoftDeleteModel` (base class)
- ⬜ Criar mixins para soft delete
- ⬜ Testar soft delete básico

### 1.4. Testes da Fase 1
- ⬜ Testes unitários: SoftDeleteManager
- ⬜ Testes unitários: SoftDeleteModel
- ⬜ Testes de integração: health check endpoints
- ⬜ Testes de configuração: settings (dev, prod)

### 1.5. Observabilidade e Monitoramento
- ⬜ Instalar e configurar Sentry
- ⬜ Configurar logging estruturado (JSON)
- ⬜ Criar endpoints de health check (`/health/`, `/health/db/`, `/health/redis/`, `/health/celery/`)
- ⬜ Configurar níveis de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- ⬜ Configurar rotação de logs

### 1.6. Documentação da Fase 1
- ⬜ Instalar `drf-yasg` ou `drf-spectacular`
- ⬜ Configurar Swagger/OpenAPI
- ⬜ Configurar endpoints de documentação (`/swagger/`, `/redoc/`, `/openapi.json`)
- ⬜ Criar README.md com instruções de setup
- ⬜ Documentar estrutura do projeto
- ⬜ Documentar variáveis de ambiente no README

---

## 🗄️ FASE 2: Banco de Dados e Modelos

### 2.1. Modelo User e Autenticação Base
- ⬜ Criar modelo `User` customizado (estender AbstractUser)
- ⬜ Adicionar campos: `created_at`, `updated_at`, `deleted_at`
- ⬜ Configurar hash de senhas com bcrypt
- ⬜ Criar migrations iniciais
- ⬜ Aplicar migrations

### 2.2. Modelos de Perfis
- ⬜ Criar modelo `ProviderProfile` (OneToOne com User)
- ⬜ Criar modelo `ClientProfile` (OneToOne com User)
- ⬜ Adicionar campos `deleted_at` em ambos
- ⬜ Criar migrations
- ⬜ Aplicar migrations

### 2.3. Modelos de Serviços
- ⬜ Criar modelo `ServiceCategory` (com parent para subcategorias)
- ⬜ Criar modelo `Service`
- ⬜ Adicionar campos `deleted_at` em ambos
- ⬜ Criar migrations
- ⬜ Aplicar migrations

### 2.4. Modelos de Pedidos e Propostas
- ⬜ Criar modelo `Order`
- ⬜ Criar modelo `Proposal`
- ⬜ Adicionar campos `deleted_at` em ambos
- ⬜ Criar migrations
- ⬜ Aplicar migrations

### 2.5. Modelos de Chat
- ⬜ Criar modelo `ChatRoom`
- ⬜ Criar modelo `Message` (com tipos: TEXT, IMAGE, FILE, SYSTEM)
- ⬜ Adicionar campos `deleted_at` em ambos
- ⬜ Criar índices necessários
- ⬜ Criar migrations
- ⬜ Aplicar migrations

### 2.6. Modelos de Assinaturas
- ⬜ Criar modelo `SubscriptionPlan`
- ⬜ Criar modelo `UserSubscription`
- ⬜ Criar modelo `SubscriptionPayment`
- ⬜ Adicionar campos `deleted_at` em todos
- ⬜ Criar migrations
- ⬜ Aplicar migrations
- ⬜ Criar dados iniciais (planos: FREE, BASIC, PREMIUM, ENTERPRISE)

### 2.7. Modelos de Pagamentos
- ⬜ Criar modelo `Payment` (pagamentos de serviços)
- ⬜ Adicionar campo `deleted_at`
- ⬜ Criar migrations
- ⬜ Aplicar migrations

### 2.8. Modelos de Reviews
- ⬜ Criar modelo `Review`
- ⬜ Adicionar campo `deleted_at`
- ⬜ Criar índice único (order, reviewer)
- ⬜ Criar migrations
- ⬜ Aplicar migrations

### 2.9. Modelos Administrativos
- ⬜ Criar modelo `AdminAction` (auditoria)
- ⬜ Criar modelo `DeviceToken` (para Firebase - futuro)
- ⬜ Adicionar campos `deleted_at` em ambos
- ⬜ Criar migrations
- ⬜ Aplicar migrations

### 2.10. Testes da Fase 2
- ⬜ Testes unitários: Modelo User (validações, métodos)
- ⬜ Testes unitários: Modelo ProviderProfile
- ⬜ Testes unitários: Modelo ClientProfile
- ⬜ Testes unitários: Modelo ServiceCategory (relacionamento self)
- ⬜ Testes unitários: Modelo Service
- ⬜ Testes unitários: Modelo Order (validações, status)
- ⬜ Testes unitários: Modelo Proposal (validações, expires_at)
- ⬜ Testes unitários: Modelo ChatRoom
- ⬜ Testes unitários: Modelo Message (tipos, is_read)
- ⬜ Testes unitários: Modelo SubscriptionPlan
- ⬜ Testes unitários: Modelo UserSubscription
- ⬜ Testes unitários: Modelo Payment
- ⬜ Testes unitários: Modelo Review (validação rating, unique constraint)
- ⬜ Testes de integração: Relacionamentos entre modelos
- ⬜ Testes de integração: Soft delete em todos os modelos

### 2.11. Documentação da Fase 2
- ⬜ Documentar modelos no Swagger (schemas)
- ⬜ Documentar relacionamentos entre modelos
- ⬜ Adicionar docstrings nos modelos
- ⬜ Documentar choices/enums (status, tipos de mensagem, etc.)

---

## 👨‍💼 FASE 3: App Admin

### 3.1. Serializers
- ⬜ Criar serializers para dashboard/stats
- ⬜ Criar serializers para relatórios

### 3.2. ViewSets
- ⬜ Criar `AdminDashboardViewSet`
- ⬜ Criar `AdminUserViewSet`
- ⬜ Criar `AdminOrderViewSet`
- ⬜ Criar `AdminProposalViewSet`
- ⬜ Criar `AdminPaymentViewSet`
- ⬜ Criar `AdminSubscriptionViewSet`
- ⬜ Criar `AdminReviewViewSet`
- ⬜ Criar `AdminAuditLogViewSet`
- ⬜ Implementar permissões (IsAdmin)
- ⬜ Implementar lógica de suspender/ativar usuários

### 3.3. Endpoints
- ⬜ GET `/admin/dashboard/stats/` - Estatísticas do dashboard
- ⬜ GET `/admin/users/` - Listar usuários
- ⬜ GET `/admin/users/{id}/` - Detalhes do usuário
- ⬜ PATCH `/admin/users/{id}/` - Atualizar usuário
- ⬜ POST `/admin/users/{id}/suspend/` - Suspender usuário
- ⬜ POST `/admin/users/{id}/activate/` - Ativar usuário
- ⬜ GET `/admin/orders/` - Listar pedidos (admin)
- ⬜ GET `/admin/proposals/` - Listar propostas (admin)
- ⬜ GET `/admin/payments/` - Listar pagamentos (admin)
- ⬜ GET `/admin/subscriptions/` - Listar assinaturas (admin)
- ⬜ GET `/admin/reviews/` - Listar reviews (admin)
- ⬜ GET `/admin/audit-logs/` - Logs de auditoria

### 3.4. Auditoria
- ⬜ Criar middleware para registrar ações administrativas
- ⬜ Implementar logging de ações (AdminAction)

### 3.5. URLs
- ⬜ Configurar URLs do app admin
- ⬜ Integrar com URLs principais

### 3.6. Testes da Fase 3
- ⬜ Testes unitários: Serializers de dashboard/stats
- ⬜ Testes de integração: AdminDashboardViewSet (estatísticas)
- ⬜ Testes de integração: AdminUserViewSet (CRUD, suspend, activate)
- ⬜ Testes de integração: AdminOrderViewSet, AdminProposalViewSet, etc.
- ⬜ Testes de integração: Permissões (IsAdmin)
- ⬜ Testes de integração: Middleware de auditoria (AdminAction)
- ⬜ Testes E2E: Admin acessa dashboard → gerencia usuários → verifica logs de auditoria

### 3.7. Documentação da Fase 3
- ⬜ Documentar endpoints do app admin no Swagger
- ⬜ Adicionar exemplos de requisições/respostas
- ⬜ Documentar permissões administrativas
- ⬜ Documentar sistema de auditoria
- ⬜ Adicionar tags "Admin" no Swagger

---

## 🔐 FASE 4: Autenticação e Permissões

### 4.1. Sistema JWT
- ⬜ Instalar e configurar `djangorestframework-simplejwt` ou `djoser`
- ⬜ Configurar access token (15-30 minutos)
- ⬜ Configurar refresh token (7 dias)
- ⬜ Configurar blacklist de tokens (Redis)
- ⬜ Implementar rotação de refresh tokens

### 4.2. Endpoints de Autenticação
- ⬜ POST `/auth/register` - Registro de usuário
- ⬜ POST `/auth/login` - Login
- ⬜ POST `/auth/refresh` - Renovar token
- ⬜ POST `/auth/logout` - Logout (blacklist token)
- ⬜ GET `/auth/me` - Dados do usuário logado
- ⬜ PATCH `/auth/me` - Atualizar dados do usuário
- ⬜ POST `/auth/password/reset` - Solicitar reset de senha
- ⬜ POST `/auth/password/reset/confirm` - Confirmar reset de senha

### 4.3. Permissões Customizadas
- ⬜ Criar `IsClient` permission
- ⬜ Criar `IsProvider` permission
- ⬜ Criar `IsAdmin` permission
- ⬜ Criar `IsProposalOwner` permission
- ⬜ Criar `IsOrderOwner` permission
- ⬜ Criar `IsChatRoomParticipant` permission
- ⬜ Criar `IsSubscriptionOwner` permission
- ⬜ Criar `HasActiveSubscription` permission
- ⬜ Criar `CanCreateOrder` permission (verifica limites)
- ⬜ Criar `CanCreateProposal` permission (verifica limites)

### 4.4. Validação de Senhas
- ⬜ Implementar validação de força de senha (mínimo 8 caracteres, letras, números, caracteres especiais)
- ⬜ Configurar bcrypt explicitamente no settings
- ⬜ Testar hash de senhas

### 4.5. Testes da Fase 4
- ⬜ Testes unitários: Sistema JWT (geração, validação, refresh)
- ⬜ Testes unitários: Permissões customizadas (IsClient, IsProvider, IsAdmin, etc.)
- ⬜ Testes unitários: Validação de força de senha
- ⬜ Testes unitários: Hash de senhas com bcrypt
- ⬜ Testes de integração: Endpoints de autenticação (register, login, refresh, logout)
- ⬜ Testes de integração: Endpoint /auth/me
- ⬜ Testes de integração: Reset de senha
- ⬜ Testes de integração: Blacklist de tokens
- ⬜ Testes E2E: Fluxo completo de registro → login → refresh → logout

### 4.6. Documentação da Fase 4
- ⬜ Documentar endpoints de autenticação no Swagger
- ⬜ Adicionar exemplos de requisições/respostas de autenticação
- ⬜ Documentar sistema de permissões
- ⬜ Documentar validação de senhas
- ⬜ Documentar uso de JWT no Swagger (autenticação)

---

## 👥 FASE 5: App Accounts

### 5.1. Serializers
- ⬜ Criar `UserSerializer`
- ⬜ Criar `UserRegistrationSerializer`
- ⬜ Criar `ProviderProfileSerializer`
- ⬜ Criar `ClientProfileSerializer`
- ⬜ Criar `UserProfileSerializer` (combinado)

### 5.2. ViewSets
- ⬜ Criar `UserViewSet` (CRUD básico)
- ⬜ Criar `ProviderProfileViewSet`
- ⬜ Criar `ClientProfileViewSet`
- ⬜ Implementar validações nos serializers

### 5.3. URLs
- ⬜ Configurar URLs do app accounts
- ⬜ Integrar com URLs principais

### 5.4. Testes da Fase 5
- ⬜ Testes unitários: Serializers (validação, transformação)
- ⬜ Testes de integração: UserViewSet (CRUD)
- ⬜ Testes de integração: ProviderProfileViewSet
- ⬜ Testes de integração: ClientProfileViewSet
- ⬜ Testes de integração: Permissões (IsClient, IsProvider)
- ⬜ Testes E2E: Criar perfil de cliente e prestador

### 5.5. Documentação da Fase 5
- ⬜ Documentar endpoints do app accounts no Swagger
- ⬜ Adicionar exemplos de requisições/respostas
- ⬜ Documentar serializers (campos, validações)
- ⬜ Adicionar tags "Accounts" no Swagger

---

## 🛍️ FASE 6: App Services

### 5.1. Serializers
- ⬜ Criar `ServiceCategorySerializer`
- ⬜ Criar `ServiceSerializer`
- ⬜ Implementar validações

### 5.2. ViewSets
- ⬜ Criar `ServiceCategoryViewSet` (CRUD - admin only para criar/editar/deletar)
- ⬜ Criar `ServiceViewSet` (CRUD - admin only para criar/editar/deletar)
- ⬜ Implementar filtros (categoria, ativo, etc.)

### 6.3. Endpoints
- ⬜ GET `/categories/` - Listar categorias
- ⬜ GET `/categories/{id}/` - Detalhes da categoria
- ⬜ POST `/categories/` - Criar categoria (admin only)
- ⬜ PATCH `/categories/{id}/` - Atualizar categoria (admin only)
- ⬜ DELETE `/categories/{id}/` - Deletar categoria (admin only)
- ⬜ GET `/categories/{id}/services/` - Serviços de uma categoria
- ⬜ GET `/services/` - Listar serviços
- ⬜ GET `/services/{id}/` - Detalhes do serviço
- ⬜ POST `/services/` - Criar serviço (admin only)
- ⬜ PATCH `/services/{id}/` - Atualizar serviço (admin only)
- ⬜ DELETE `/services/{id}/` - Deletar serviço (admin only)

### 6.4. URLs
- ⬜ Configurar URLs do app services
- ⬜ Integrar com URLs principais

### 6.5. Testes da Fase 6
- ⬜ Testes unitários: Serializers (validações)
- ⬜ Testes de integração: ServiceCategoryViewSet (CRUD, filtros)
- ⬜ Testes de integração: ServiceViewSet (CRUD, filtros)
- ⬜ Testes de integração: Permissões (admin only para criar/editar/deletar)
- ⬜ Testes de integração: Endpoint /categories/{id}/services/
- ⬜ Testes E2E: Criar categoria → criar serviço → listar serviços da categoria

### 6.6. Documentação da Fase 6
- ⬜ Documentar endpoints do app services no Swagger
- ⬜ Adicionar exemplos de requisições/respostas
- ⬜ Documentar filtros disponíveis
- ⬜ Adicionar tags "Services" no Swagger

---

## 📦 FASE 7: App Orders

### 7.1. Serializers
- ⬜ Criar `OrderSerializer`
- ⬜ Criar `OrderCreateSerializer`
- ⬜ Criar `OrderStatusUpdateSerializer`
- ⬜ Implementar validações (budget_min < budget_max, deadline no futuro)

### 7.2. ViewSets
- ⬜ Criar `OrderViewSet`
- ⬜ Implementar filtros (status, service, client)
- ⬜ Implementar verificação de limites de assinatura antes de criar
- ⬜ Implementar permissões (IsOrderOwner, CanCreateOrder)

### 6.3. Endpoints
- ⬜ GET `/orders/` - Listar pedidos (com filtros)
- ⬜ POST `/orders/` - Criar pedido (client only, verifica limite)
- ⬜ GET `/orders/{id}/` - Detalhes do pedido
- ⬜ PATCH `/orders/{id}/status/` - Atualizar status (owner only)
- ⬜ DELETE `/orders/{id}/` - Deletar pedido (owner only, apenas se PENDING)
- ⬜ GET `/orders/{id}/proposals/` - Propostas de um pedido

### 6.4. URLs
- ⬜ Configurar URLs do app orders
- ⬜ Integrar com URLs principais

### 6.5. Testes da Fase 6
- ⬜ Testes unitários: Serializers (validações: budget_min < budget_max, deadline no futuro)
- ⬜ Testes de integração: OrderViewSet (CRUD, filtros)
- ⬜ Testes de integração: Verificação de limites de assinatura
- ⬜ Testes de integração: Permissões (IsOrderOwner, CanCreateOrder)
- ⬜ Testes de integração: Endpoint /orders/{id}/proposals/
- ⬜ Testes E2E: Cliente cria pedido → verifica limites → lista pedidos

### 6.6. Documentação da Fase 6
- ⬜ Documentar endpoints do app orders no Swagger
- ⬜ Adicionar exemplos de requisições/respostas
- ⬜ Documentar filtros disponíveis
- ⬜ Documentar validações (budget, deadline)
- ⬜ Documentar verificação de limites de assinatura
- ⬜ Adicionar tags "Orders" no Swagger

---

## 💼 FASE 8: App Proposals

### 7.1. Serializers
- ⬜ Criar `ProposalSerializer`
- ⬜ Criar `ProposalCreateSerializer`
- ⬜ Implementar validações (price > 0, estimated_days > 0, expires_at no futuro)

### 7.2. ViewSets
- ⬜ Criar `ProposalViewSet`
- ⬜ Implementar filtros (order, provider, status)
- ⬜ Implementar verificação de limites de assinatura antes de criar
- ⬜ Implementar permissões (IsProposalOwner, CanCreateProposal)
- ⬜ Implementar lógica de aceitar/recusar proposta

### 8.3. Endpoints
- ⬜ GET `/proposals/` - Listar propostas (com filtros)
- ⬜ POST `/proposals/` - Criar proposta (provider only, verifica limite)
- ⬜ GET `/proposals/{id}/` - Detalhes da proposta
- ⬜ PATCH `/proposals/{id}/accept` - Aceitar proposta (order owner only)
- ⬜ PATCH `/proposals/{id}/decline` - Recusar proposta (order owner only)
- ⬜ DELETE `/proposals/{id}/` - Deletar proposta (owner only, apenas se PENDING)

### 8.4. URLs
- ⬜ Configurar URLs do app proposals
- ⬜ Integrar com URLs principais

### 8.5. Testes da Fase 8
- ⬜ Testes unitários: Serializers (validações: price > 0, estimated_days > 0, expires_at no futuro)
- ⬜ Testes de integração: ProposalViewSet (CRUD, filtros)
- ⬜ Testes de integração: Verificação de limites de assinatura
- ⬜ Testes de integração: Permissões (IsProposalOwner, CanCreateProposal)
- ⬜ Testes de integração: Aceitar proposta (lógica de negócio)
- ⬜ Testes de integração: Recusar proposta
- ⬜ Testes E2E: Prestador cria proposta → cliente aceita → verifica status

### 8.6. Documentação da Fase 8
- ⬜ Documentar endpoints do app proposals no Swagger
- ⬜ Adicionar exemplos de requisições/respostas
- ⬜ Documentar filtros disponíveis
- ⬜ Documentar validações (price, estimated_days, expires_at)
- ⬜ Documentar lógica de aceitar/recusar proposta
- ⬜ Adicionar tags "Proposals" no Swagger

---

## 💬 FASE 9: App Chat

### 9.1. Serializers
- ⬜ Criar `ChatRoomSerializer`
- ⬜ Criar `MessageSerializer`
- ⬜ Criar `MessageCreateSerializer`
- ⬜ Implementar validações

### 9.2. ViewSets
- ⬜ Criar `ChatRoomViewSet`
- ⬜ Criar `MessageViewSet`
- ⬜ Implementar lógica de criação automática de ChatRoom
- ⬜ Implementar permissões (IsChatRoomParticipant)
- ⬜ Implementar marcação de mensagens como lidas

### 9.3. Endpoints REST
- ⬜ GET `/chat/rooms/` - Listar salas do usuário
- ⬜ GET `/chat/rooms/{id}/` - Detalhes da sala
- ⬜ POST `/chat/rooms/` - Criar sala para um pedido
- ⬜ GET `/chat/rooms/{id}/messages/` - Mensagens de uma sala
- ⬜ POST `/chat/rooms/{id}/messages/` - Enviar mensagem
- ⬜ PATCH `/chat/rooms/{id}/messages/{message_id}/read` - Marcar como lida
- ⬜ GET `/chat/rooms/{id}/unread-count/` - Contador de não lidas

### 9.4. WebSocket (Django Channels)
- ⬜ Instalar e configurar Django Channels
- ⬜ Configurar ASGI
- ⬜ Criar consumer para chat
- ⬜ Implementar eventos: connect, disconnect, send_message, receive_message, mark_read, typing, user_online, user_offline
- ⬜ Configurar WebSocket: `/ws/chat/{room_id}/`

### 9.5. URLs
- ⬜ Configurar URLs do app chat
- ⬜ Integrar com URLs principais

### 9.6. Testes da Fase 9
- ⬜ Testes unitários: Serializers (validações)
- ⬜ Testes de integração: ChatRoomViewSet (CRUD)
- ⬜ Testes de integração: MessageViewSet (CRUD)
- ⬜ Testes de integração: Criação automática de ChatRoom
- ⬜ Testes de integração: Permissões (IsChatRoomParticipant)
- ⬜ Testes de integração: Marcação de mensagens como lidas
- ⬜ Testes de integração: Contador de mensagens não lidas
- ⬜ Testes de integração: WebSocket consumer (connect, disconnect, send_message, receive_message)
- ⬜ Testes E2E: Criar sala → enviar mensagens → marcar como lida → WebSocket

### 9.7. Documentação da Fase 9
- ⬜ Documentar endpoints do app chat no Swagger
- ⬜ Adicionar exemplos de requisições/respostas
- ⬜ Documentar tipos de mensagem (TEXT, IMAGE, FILE, SYSTEM)
- ⬜ Documentar WebSocket events e protocolo
- ⬜ Documentar criação automática de ChatRoom
- ⬜ Adicionar tags "Chat" no Swagger

---

## 💳 FASE 10: App Subscriptions

### 9.1. Serializers
- ⬜ Criar `SubscriptionPlanSerializer`
- ⬜ Criar `UserSubscriptionSerializer`
- ⬜ Criar `SubscriptionPaymentSerializer`
- ⬜ Criar `SubscriptionUsageSerializer`
- ⬜ Implementar validações

### 9.2. ViewSets
- ⬜ Criar `SubscriptionPlanViewSet` (admin only para criar/editar)
- ⬜ Criar `UserSubscriptionViewSet`
- ⬜ Criar `SubscriptionPaymentViewSet`
- ⬜ Implementar lógica de assinatura automática (FREE para novos usuários)
- ⬜ Implementar lógica de upgrade/downgrade
- ⬜ Implementar lógica de cancelamento
- ⬜ Implementar cálculo de uso vs limites

### 10.3. Middleware/Decorators
- ⬜ Criar decorator para verificar limites de assinatura
- ⬜ Criar middleware para verificar limites (opcional)

### 10.4. Endpoints
- ⬜ GET `/subscriptions/plans/` - Listar planos
- ⬜ GET `/subscriptions/plans/{id}/` - Detalhes do plano
- ⬜ POST `/subscriptions/plans/` - Criar plano (admin only)
- ⬜ PATCH `/subscriptions/plans/{id}/` - Atualizar plano (admin only)
- ⬜ GET `/subscriptions/my-subscription/` - Minha assinatura
- ⬜ POST `/subscriptions/subscribe/` - Escolher plano
- ⬜ PATCH `/subscriptions/my-subscription/cancel/` - Cancelar assinatura
- ⬜ PATCH `/subscriptions/my-subscription/reactivate/` - Reativar assinatura
- ⬜ GET `/subscriptions/my-subscription/payments/` - Pagamentos da assinatura
- ⬜ GET `/subscriptions/my-subscription/usage/` - Uso atual vs limites

### 9.5. URLs
- ⬜ Configurar URLs do app subscriptions
- ⬜ Integrar com URLs principais

### 9.6. Testes da Fase 9
- ⬜ Testes unitários: Serializers (validações)
- ⬜ Testes de integração: SubscriptionPlanViewSet
- ⬜ Testes de integração: UserSubscriptionViewSet
- ⬜ Testes de integração: Assinatura automática (FREE para novos usuários)
- ⬜ Testes de integração: Upgrade/downgrade de plano
- ⬜ Testes de integração: Cancelamento de assinatura
- ⬜ Testes de integração: Cálculo de uso vs limites
- ⬜ Testes de integração: Decorator/middleware de verificação de limites
- ⬜ Testes E2E: Assinar plano → verificar limites → upgrade → cancelar

### 9.7. Documentação da Fase 9
- ⬜ Documentar endpoints do app subscriptions no Swagger
- ⬜ Adicionar exemplos de requisições/respostas
- ⬜ Documentar planos disponíveis e seus limites
- ⬜ Documentar lógica de upgrade/downgrade
- ⬜ Documentar cálculo de uso
- ⬜ Adicionar tags "Subscriptions" no Swagger

---

## 💰 FASE 11: App Payments

### 11.1. Serializers
- ⬜ Criar `PaymentSerializer`
- ⬜ Criar `PaymentCreateSerializer` (simulação)
- ⬜ Implementar validações (amount > 0, payment_date não no passado)

### 11.2. ViewSets
- ⬜ Criar `PaymentViewSet`
- ⬜ Implementar lógica de simulação de pagamento
- ⬜ Implementar filtros (order, status)
- ⬜ Implementar permissões (admin only para status e refund)

### 11.3. Endpoints
- ⬜ GET `/payments/` - Listar pagamentos (com filtros)
- ⬜ POST `/payments/` - Criar pagamento (simulação)
- ⬜ GET `/payments/{id}/` - Detalhes do pagamento
- ⬜ PATCH `/payments/{id}/status/` - Atualizar status (admin only)
- ⬜ POST `/payments/{id}/refund/` - Reembolsar (admin only)

### 11.4. URLs
- ⬜ Configurar URLs do app payments
- ⬜ Integrar com URLs principais

### 11.5. Testes da Fase 11
- ⬜ Testes unitários: Serializers (validações: amount > 0, payment_date não no passado)
- ⬜ Testes de integração: PaymentViewSet (CRUD, filtros)
- ⬜ Testes de integração: Lógica de simulação de pagamento
- ⬜ Testes de integração: Permissões (admin only para status e refund)
- ⬜ Testes de integração: Reembolso
- ⬜ Testes E2E: Criar pagamento → atualizar status → reembolsar

### 11.6. Documentação da Fase 11
- ⬜ Documentar endpoints do app payments no Swagger
- ⬜ Adicionar exemplos de requisições/respostas
- ⬜ Documentar simulação de pagamento
- ⬜ Documentar status de pagamento
- ⬜ Documentar processo de reembolso
- ⬜ Adicionar tags "Payments" no Swagger

---

## ⭐ FASE 12: App Reviews

### 12.1. Serializers
- ⬜ Criar `ReviewSerializer`
- ⬜ Criar `ReviewCreateSerializer`
- ⬜ Implementar validações (rating 1-5, apenas uma review por order)

### 12.2. ViewSets
- ⬜ Criar `ReviewViewSet`
- ⬜ Implementar filtros (reviewed_user, order)
- ⬜ Implementar permissões (IsOrderOwner para criar, owner para editar/deletar)
- ⬜ Implementar lógica de atualização de rating do prestador

### 12.3. Endpoints
- ⬜ GET `/reviews/` - Listar reviews (com filtros)
- ⬜ POST `/orders/{id}/review` - Criar review (order owner only, após conclusão)
- ⬜ GET `/reviews/{id}/` - Detalhes da review
- ⬜ PATCH `/reviews/{id}/` - Atualizar review (owner only)
- ⬜ DELETE `/reviews/{id}/` - Deletar review (owner only)

### 12.4. URLs
- ⬜ Configurar URLs do app reviews
- ⬜ Integrar com URLs principais

### 12.5. Testes da Fase 12
- ⬜ Testes unitários: Serializers (validações: rating 1-5, apenas uma review por order)
- ⬜ Testes de integração: ReviewViewSet (CRUD, filtros)
- ⬜ Testes de integração: Permissões (IsOrderOwner para criar, owner para editar/deletar)
- ⬜ Testes de integração: Atualização de rating do prestador
- ⬜ Testes de integração: Constraint unique (order, reviewer)
- ⬜ Testes E2E: Criar review → verificar atualização de rating → tentar criar segunda review (deve falhar)

### 12.6. Documentação da Fase 12
- ⬜ Documentar endpoints do app reviews no Swagger
- ⬜ Adicionar exemplos de requisições/respostas
- ⬜ Documentar validações (rating, constraint unique)
- ⬜ Documentar atualização de rating do prestador
- ⬜ Adicionar tags "Reviews" no Swagger

---

## 📧 FASE 13: App Notifications (Celery)

### 13.1. Configuração Celery
- ⬜ Instalar Celery e Redis
- ⬜ Configurar `celery.py`
- ⬜ Configurar broker (Redis)
- ⬜ Configurar result backend (Redis)
- ⬜ Configurar filas (emails, push_notifications, heavy_tasks, maintenance, logging)
- ⬜ Configurar retry automático
- ⬜ Configurar dead letter queue

### 13.2. Tasks de Email
- ⬜ Criar task: enviar email quando cliente cria pedido
- ⬜ Criar task: enviar email quando prestador recebe proposta nova
- ⬜ Criar task: enviar email de notificação de nova mensagem no chat
- ⬜ Criar task: enviar email de boas-vindas ao registrar
- ⬜ Criar task: enviar email de confirmação de pagamento
- ⬜ Criar task: enviar email de vencimento de assinatura (7 dias antes, 1 dia antes)
- ⬜ Criar task: enviar email de renovação de assinatura
- ⬜ Criar task: enviar email de lembretes (pedidos pendentes, propostas expiradas)
- ⬜ Criar task: enviar email de recuperação de senha
- ⬜ Criar task: enviar email de notificações administrativas
- ⬜ Configurar templates de email

### 13.3. Tasks de Processamento Pesado
- ⬜ Criar task: calcular ranking dos prestadores (periódica - diária)
- ⬜ Criar task: gerar relatórios administrativos (periódica - semanal/mensal)
- ⬜ Criar task: processar uploads de arquivos grandes
- ⬜ Criar task: gerar PDFs de propostas

### 13.4. Tasks de Manutenção
- ⬜ Criar task: limpar propostas expiradas (periódica)
- ⬜ Criar task: processar renovações de assinatura (periódica - diária)
- ⬜ Criar task: resetar contadores mensais de assinaturas (periódica - primeiro dia do mês)
- ⬜ Criar task: limpar tokens expirados
- ⬜ Criar task: limpar sessões antigas
- ⬜ Criar task: backup de dados

### 13.5. Tasks de Logging
- ⬜ Criar task: gerar logs e histórico
- ⬜ Criar task: auditoria de eventos
- ⬜ Criar task: métricas e analytics

### 13.6. Monitoramento Celery
- ⬜ Instalar e configurar Flower
- ⬜ Configurar logs de tarefas executadas
- ⬜ Configurar alertas para tarefas que falharam
- ⬜ Configurar métricas de performance das filas

### 13.7. Integração com Views
- ⬜ Integrar tasks de email nos ViewSets apropriados
- ⬜ Configurar triggers automáticos

### 13.8. Testes da Fase 13
- ⬜ Testes unitários: Tasks de email (mock de envio)
- ⬜ Testes unitários: Tasks de processamento pesado (mock de dependências)
- ⬜ Testes unitários: Tasks de manutenção
- ⬜ Testes de integração: Execução de tasks (com Celery em modo de teste)
- ⬜ Testes de integração: Retry automático
- ⬜ Testes de integração: Dead letter queue
- ⬜ Testes de integração: Tasks periódicas
- ⬜ Testes E2E: Trigger de task → verificar execução → verificar resultado

### 13.9. Documentação da Fase 13
- ⬜ Documentar tasks do Celery
- ⬜ Documentar filas e suas funções
- ⬜ Documentar configuração do Celery
- ⬜ Documentar monitoramento com Flower
- ⬜ Adicionar seção sobre tasks no README

---

## 🔒 FASE 14: Segurança e Validações

### 14.1. Validações de Dados
- ⬜ Implementar validações em todos os serializers
- ⬜ Validação de formatos (email, telefone, CPF/CNPJ)
- ⬜ Validação de ranges (valores mínimos/máximos)
- ⬜ Validação customizada com métodos `validate_<campo>()`
- ⬜ Validação de relacionamentos (FKs existentes)

### 14.2. Constraints no Banco
- ⬜ Adicionar constraints unique onde necessário
- ⬜ Adicionar constraints check onde necessário
- ⬜ Criar migrations para constraints

### 14.3. Transações Atômicas
- ⬜ Implementar transações atômicas para operações críticas
- ⬜ Validar estado antes de mudanças (ex: não aceitar proposta já aceita)

### 14.4. Segurança Adicional
- ⬜ Configurar CORS adequadamente
- ⬜ Configurar rate limiting (DRF throttling)
- ⬜ Configurar headers de segurança (X-Content-Type-Options, X-Frame-Options, etc.)
- ⬜ Implementar validação de tamanho de uploads
- ⬜ Configurar logs de segurança (tentativas de login falhadas)
- ⬜ Implementar proteção contra SQL injection (usar apenas ORM seguro)

### 14.5. Testes da Fase 14
- ⬜ Testes de segurança: Validações de dados (todos os serializers)
- ⬜ Testes de segurança: Constraints no banco
- ⬜ Testes de segurança: Transações atômicas
- ⬜ Testes de segurança: Rate limiting
- ⬜ Testes de segurança: CORS
- ⬜ Testes de segurança: Headers de segurança
- ⬜ Testes de segurança: Proteção contra SQL injection
- ⬜ Testes de segurança: Logs de tentativas de login falhadas

### 14.6. Documentação da Fase 14
- ⬜ Documentar medidas de segurança implementadas
- ⬜ Documentar validações de dados
- ⬜ Documentar rate limiting
- ⬜ Adicionar seção de segurança no README

---

## 🧪 FASE 15: Setup de Testes e CI/CD

### 15.1. Setup de Testes
- ⬜ Instalar pytest e dependências (pytest-django, pytest-cov, factory-boy, faker, freezegun, responses, django-test-plus)
- ⬜ Configurar pytest.ini
- ⬜ Configurar factories com factory-boy
- ⬜ Configurar fixtures
- ⬜ Configurar cobertura de código (pytest-cov)

### 15.2. Testes E2E de Fluxos Completos
- ⬜ Teste E2E: Registro → Login → Criar pedido → Receber proposta → Aceitar → Pagar → Review
- ⬜ Teste E2E: Assinatura → Upgrade → Cancelamento
- ⬜ Teste E2E: Chat completo (criar sala → enviar mensagens → marcar como lida)
- ⬜ Mock de serviços externos (email, Firebase, gateways de pagamento)

### 15.3. CI/CD
- ⬜ Configurar pipeline CI/CD (GitHub Actions, GitLab CI, etc.)
- ⬜ Executar testes automaticamente em cada commit/PR
- ⬜ Verificar cobertura de código (mínimo 80%)
- ⬜ Executar linters (flake8, black, isort)
- ⬜ Executar testes de segurança (bandit, safety)
- ⬜ Configurar notificações de falhas nos testes

---

## 📚 FASE 16: Documentação Final e Revisão

### 16.1. Revisão da Documentação Swagger
- ⬜ Revisar documentação de todos os endpoints no Swagger
- ⬜ Verificar exemplos de requisições e respostas
- ⬜ Verificar documentação de códigos de erro
- ⬜ Verificar descrições detalhadas nos serializers
- ⬜ Verificar tags para organização
- ⬜ Verificar documentação de autenticação
- ⬜ Adicionar exemplos de uso complexos

### 16.2. Documentação do Projeto
- ⬜ Revisar e atualizar README.md com instruções completas
- ⬜ Documentar variáveis de ambiente (completo)
- ⬜ Documentar setup de desenvolvimento (completo)
- ⬜ Documentar deploy (completo)
- ⬜ Criar CHANGELOG.md
- ⬜ Criar CONTRIBUTING.md (se aplicável)
- ⬜ Documentar arquitetura do projeto

---

## 🚀 FASE 17: Deploy e Produção

### 17.1. Preparação para Produção
- ⬜ Configurar settings de produção
- ⬜ Configurar HTTPS
- ⬜ Configurar variáveis de ambiente de produção
- ⬜ Configurar backup de banco de dados
- ⬜ Configurar backup criptografado de dados sensíveis

### 17.2. Docker (Opcional)
- ⬜ Criar Dockerfile
- ⬜ Criar docker-compose.yml
- ⬜ Configurar serviços (app, db, redis, celery)
- ⬜ Testar localmente com Docker

### 17.3. Deploy
- ⬜ Escolher plataforma de deploy (Heroku, AWS, DigitalOcean, etc.)
- ⬜ Configurar ambiente de produção
- ⬜ Configurar banco de dados de produção
- ⬜ Configurar Redis de produção
- ⬜ Configurar workers Celery de produção
- ⬜ Configurar Sentry de produção
- ⬜ Fazer deploy inicial
- ⬜ Testar em produção

---

## 🔮 FASE 18: Recursos Futuros (Opcional)

### 18.1. Notificações Push (Firebase)
- ⬜ Instalar `firebase-admin` SDK
- ⬜ Configurar credenciais do Firebase no settings
- ⬜ Criar serviço de notificações push
- ⬜ Implementar endpoints para gerenciar tokens de dispositivos
- ⬜ Criar tasks de notificação push
- ⬜ Tratar erros de tokens inválidos/expirados

### 18.2. Outros Recursos
- ⬜ Integração com gateways de pagamento reais (Stripe, Asaas, Mercado Pago)
- ⬜ Cache com Redis (para categorias, serviços, rankings)
- ⬜ Upload de arquivos para S3
- ⬜ API de webhooks para integrações externas
- ⬜ Sistema de cupons/descontos para assinaturas
- ⬜ Analytics e tracking de eventos
- ⬜ Sistema de tags para pedidos e serviços
- ⬜ Busca avançada com Elasticsearch
- ⬜ Sistema de favoritos (prestadores favoritos)
- ⬜ Histórico de visualizações

---

## 📝 Notas

- As tarefas estão organizadas por fases lógicas de desenvolvimento
- **Testes e Documentação**: Cada fase possui suas próprias subseções de testes e documentação. Isso garante que cada funcionalidade seja testada e documentada conforme é desenvolvida.
- **Fase 15**: Setup inicial de testes e CI/CD, além de testes E2E de fluxos completos que envolvem múltiplos apps
- **Fase 16**: Revisão final da documentação e consolidação
- Priorize as fases 1-16 para ter um MVP funcional
- A fase 17 (Deploy) pode ser feita em paralelo com as fases anteriores
- A fase 18 (Recursos Futuros) é opcional e pode ser implementada conforme necessidade
- Atualize o status das tarefas conforme o progresso do projeto
- **Cobertura de testes**: Almeje pelo menos 80% de cobertura de código

