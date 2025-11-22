Projeto de uma plataforma de Marketplace de Serviços utilizando Django Rest Framework

**Nota**: Este é um projeto de API REST pura, sem views/telas. Toda comunicação será via endpoints REST e WebSocket.

✅ 1. Objetivo do Projeto

Criar um backend que gerencie:

- Clientes que precisam de serviços

- Prestadores que oferecem serviços

- Serviços (categorias, subcategorias)

- Pedidos de serviço

- Propostas feitas pelos prestadores

- Chat entre cliente e prestador (websocket para comunicação em tempo real)

- Sistema de assinaturas (planos, registro de assinaturas e pagamentos)

- Sistema de pagamentos de serviços (iniciando apenas com uma simulação, todos os usuários cadastrados terão assinatura gratuíta inicialmente)

- Rating / reviews

- Sistema administrativo para gerenciamento da plataforma

- Jobs assíncronos (emails, ranking, logs atuando em um sistema de filas)


✅ 2. Estrutura Recomendada do Projeto
2.1. Proposta de arquitetura de pasta base

marketplace/
│─ api/
│   ├── accounts/         (usuários, perfis, auth)
│   ├── services/         (categorias, serviços)
│   ├── orders/           (pedidos e propostas)
│   ├── chat/             (mensagens entre usuários - melhorado)
│   ├── subscriptions/    (planos, assinaturas, pagamentos de assinaturas)
│   ├── payments/         (pagamentos de serviços - simulação ou gateway real)
│   ├── reviews/          (avaliações)
│   ├── admin/            (gerenciamento administrativo)
│   ├── notifications/    (jobs de email, push notifications - Firebase preparado)
│   └── utils/            (helpers, mixins, managers - soft delete)
│
│─ config/
│   ├── settings/
│   │    ├── base.py
│   │    ├── dev.py
│   │    └── prod.py
│   └── urls.py
│
├── requirements.txt
├── celery.py
├── manage.py
└── Dockerfile (opcional)


✅ 3. Banco de Dados: Diagrama ER (completo e melhorado)

Entidades Principais:

- User (usuário base do sistema)
  - Campos: id, email, password, first_name, last_name, phone, is_active, is_staff, is_superuser, date_joined, last_login, created_at, updated_at, deleted_at
  - Tipos: CLIENT, PROVIDER, ADMIN
  - Soft Delete: Sim (deleted_at)

- ProviderProfile (prestador)
  - Campos: user (OneToOne), bio, rating_avg, total_reviews, total_orders_completed, is_verified, created_at, updated_at, deleted_at
  - Soft Delete: Sim (deleted_at)

- ClientProfile
  - Campos: user (OneToOne), address, city, state, zip_code, created_at, updated_at, deleted_at
  - Soft Delete: Sim (deleted_at)

- ServiceCategory
  - Campos: id, name, slug, description, parent (ForeignKey self - para subcategorias), is_active, created_at, updated_at, deleted_at
  - Soft Delete: Sim (deleted_at)

- Service
  - Campos: id, category (ForeignKey), name, description, is_active, created_at, updated_at, deleted_at
  - Soft Delete: Sim (deleted_at)

- Order (pedido feito pelo cliente)
  - Campos: id, client (ForeignKey ClientProfile), service (ForeignKey Service), title, description, budget_min, budget_max, deadline, status (PENDING, ACCEPTED, IN_PROGRESS, COMPLETED, CANCELLED), created_at, updated_at, deleted_at
  - Soft Delete: Sim (deleted_at)

- Proposal (resposta do prestador ao pedido)
  - Campos: id, order (ForeignKey), provider (ForeignKey ProviderProfile), message, price, estimated_days, status (PENDING, ACCEPTED, DECLINED, EXPIRED), created_at, updated_at, expires_at, deleted_at
  - Soft Delete: Sim (deleted_at)

- ChatRoom (sala de chat - MELHORADO)
  - Campos: id, order (ForeignKey Order), client (ForeignKey User), provider (ForeignKey User), created_at, updated_at, last_message_at, deleted_at
  - Índice único: (order, client, provider)
  - Soft Delete: Sim (deleted_at)

- Message (mensagem do chat - MELHORADO)
  - Campos: id, room (ForeignKey ChatRoom), sender (ForeignKey User), content, message_type (TEXT, IMAGE, FILE, SYSTEM), is_read, read_at, created_at, updated_at, deleted_at
  - Índices: room, sender, created_at, is_read
  - Soft Delete: Sim (deleted_at)

- SubscriptionPlan (planos de assinatura - NOVO)
  - Campos: id, name, slug, description, price_monthly, price_yearly, features (JSONField), max_orders_per_month, max_proposals_per_order, is_active, is_default, created_at, updated_at, deleted_at
  - Exemplos: FREE, BASIC, PREMIUM, ENTERPRISE
  - Soft Delete: Sim (deleted_at) - Nota: Planos ativos não devem ser deletados, apenas desativados

- UserSubscription (assinatura do usuário - NOVO)
  - Campos: id, user (ForeignKey User), plan (ForeignKey SubscriptionPlan), status (ACTIVE, CANCELLED, EXPIRED, SUSPENDED), start_date, end_date, auto_renew, created_at, updated_at, cancelled_at, deleted_at
  - Soft Delete: Sim (deleted_at)

- SubscriptionPayment (pagamento de assinatura - NOVO)
  - Campos: id, subscription (ForeignKey UserSubscription), amount, payment_method, payment_status (PENDING, PAID, FAILED, REFUNDED), transaction_id, payment_date, due_date, metadata (JSONField), created_at, updated_at, deleted_at
  - Soft Delete: Sim (deleted_at) - Nota: Pagamentos não devem ser deletados, apenas marcados como deletados para auditoria

- Payment (pagamento de serviço - MELHORADO)
  - Campos: id, order (ForeignKey Order), proposal (ForeignKey Proposal), amount, payment_method, payment_status (PENDING, PAID, FAILED, REFUNDED), transaction_id, payment_date, metadata (JSONField), created_at, updated_at, deleted_at
  - Soft Delete: Sim (deleted_at) - Nota: Pagamentos não devem ser deletados, apenas marcados como deletados para auditoria

- Review (avaliação)
  - Campos: id, order (ForeignKey Order), reviewer (ForeignKey User), reviewed_user (ForeignKey User), rating (1-5), comment, created_at, updated_at, deleted_at
  - Índice único: (order, reviewer)
  - Soft Delete: Sim (deleted_at)

- AdminAction (auditoria de ações administrativas - NOVO)
  - Campos: id, admin_user (ForeignKey User), action_type, target_model, target_id, description, metadata (JSONField), ip_address, created_at, deleted_at
  - Soft Delete: Sim (deleted_at) - Nota: Logs de auditoria raramente são deletados, apenas em casos específicos

- DeviceToken (tokens FCM para notificações push - NOVO)
  - Campos: id, user (ForeignKey User), token (único), device_type (IOS, ANDROID, WEB), device_id, is_active, created_at, updated_at, deleted_at
  - Soft Delete: Sim (deleted_at)
  - Nota: Preparado para integração futura com Firebase Cloud Messaging

Relacionamentos (detalhados):

- User 1–1 ProviderProfile (opcional)
- User 1–1 ClientProfile (opcional)
- User 1–N UserSubscription (histórico de assinaturas)
- User 1–N AdminAction (se for admin)
- User 1–N DeviceToken (tokens FCM para push notifications)

- ServiceCategory 1–N ServiceCategory (self - subcategorias)
- ServiceCategory 1–N Service

- ClientProfile 1–N Order
- Service 1–N Order

- Order 1–N Proposal
- Order 1–1 ChatRoom
- Order 1–1 Payment (pagamento do serviço)
- Order 1–1 Review

- ProviderProfile 1–N Proposal
- Proposal 1–1 Payment (quando aceita)

- ChatRoom 1–N Message
- User 1–N Message (como sender)

- SubscriptionPlan 1–N UserSubscription
- UserSubscription 1–N SubscriptionPayment

Observações importantes:
- Um usuário pode ser CLIENT e PROVIDER ao mesmo tempo
- ChatRoom é criado automaticamente quando uma proposta é aceita ou quando cliente/prestador iniciam conversa
- Sistema de assinaturas permite controle de limites (ex: plano FREE = 5 pedidos/mês)
- Pagamentos de assinatura são separados de pagamentos de serviços
- **Soft Delete**: Todas as tabelas possuem campo `deleted_at` (DateTimeField, nullable) para soft delete
  * Quando `deleted_at` é NULL, o registro está ativo
  * Quando `deleted_at` tem valor, o registro está deletado (mas permanece no banco)
  * Queries devem filtrar automaticamente registros deletados (usar Manager customizado)
  * Alguns registros críticos (pagamentos, logs) não devem ser deletados, apenas marcados


✅ 4. Autenticação e Permissões

Recomendações:

Use djoser ou simplejwt para JWT.

4.1. Sistema de Tokens JWT:

- Access Token: Expiração curta (15-30 minutos)
- Refresh Token: Expiração longa (7-30 dias)
- Renovação automática:
  * Middleware ou interceptor no frontend detecta token próximo do vencimento
  * Faz requisição automática para `/auth/refresh` antes do token expirar
  * Se refresh falhar, redireciona para login
  * Implementar retry logic para requisições que falharam por token expirado

- Configuração recomendada:
  * Access token: 15 minutos
  * Refresh token: 7 dias
  * Rotação de refresh tokens (opcional, mas recomendado)
  * Blacklist de tokens revogados (usar Redis)

4.2. Hash de Senhas:

- **SEMPRE usar bcrypt** para hash de senhas
- Django já usa PBKDF2 por padrão, mas podemos configurar bcrypt explicitamente
- Configuração: `PASSWORD_HASHERS` no settings
- Nunca armazenar senhas em texto plano
- Validação de força de senha no registro (mínimo 8 caracteres, letras, números, caracteres especiais)

4.3. Permissões personalizadas:

- IsClient (verifica se user tem ClientProfile)
- IsProvider (verifica se user tem ProviderProfile)
- IsAdmin (verifica se user é admin/staff)
- IsProposalOwner (verifica se user é dono da proposta)
- IsOrderOwner (verifica se user é dono do pedido)
- IsChatRoomParticipant (verifica se user participa da sala de chat)
- IsSubscriptionOwner (verifica se user é dono da assinatura)
- HasActiveSubscription (verifica se user tem assinatura ativa)
- CanCreateOrder (verifica limites do plano de assinatura)
- CanCreateProposal (verifica limites do plano de assinatura)


✅ 5. Sistema de Chat (MELHORADO)

5.1. Arquitetura do Chat

- ChatRoom: Representa uma conversa entre cliente e prestador relacionada a um pedido
- Message: Mensagens individuais dentro de uma sala
- WebSocket: Django Channels para comunicação em tempo real

5.2. Funcionalidades:

- Criação automática de ChatRoom quando:
  * Cliente inicia conversa sobre um pedido
  * Prestador envia primeira proposta
  * Proposta é aceita

- Tipos de mensagem:
  * TEXT: Mensagem de texto normal
  * IMAGE: Imagem (URL ou arquivo)
  * FILE: Arquivo anexado
  * SYSTEM: Mensagem automática do sistema (ex: "Proposta aceita")

- Status de leitura:
  * Campo is_read para marcar mensagens lidas
  * Campo read_at para timestamp de leitura
  * Endpoint para marcar mensagens como lidas

- Notificações:
  * Notificação em tempo real via WebSocket quando nova mensagem chega
  * Email de notificação se usuário estiver offline

- Busca e filtros:
  * Buscar mensagens por conteúdo
  * Filtrar por tipo de mensagem
  * Ordenar por data (mais recente primeiro)

5.3. WebSocket Events:

- connect: Usuário conecta ao chat
- disconnect: Usuário desconecta
- send_message: Enviar mensagem
- receive_message: Receber mensagem
- mark_read: Marcar mensagens como lidas
- typing: Indicador de digitação
- user_online: Usuário ficou online
- user_offline: Usuário ficou offline


✅ 6. Sistema de Assinaturas (NOVO)

6.1. Planos de Assinatura:

Planos pré-definidos:
- FREE (Gratuito):
  * 5 pedidos por mês
  * 3 propostas por pedido
  * Chat básico
  * Sem suporte prioritário

- BASIC (Básico):
  * 20 pedidos por mês
  * 10 propostas por pedido
  * Chat completo
  * Suporte por email

- PREMIUM (Premium):
  * Pedidos ilimitados
  * Propostas ilimitadas
  * Chat completo + notificações push
  * Suporte prioritário
  * Badge de verificação

- ENTERPRISE (Empresarial):
  * Tudo do Premium
  * API personalizada
  * Suporte dedicado
  * Relatórios avançados

6.2. Funcionalidades:

- Assinatura automática:
  * Usuários novos recebem plano FREE automaticamente
  * Renovação automática configurável

- Controle de limites:
  * Middleware ou decorator para verificar limites antes de criar pedido/proposta
  * Reset mensal de contadores

- Histórico de pagamentos:
  * Registro de todos os pagamentos de assinatura
  * Status de pagamento (pendente, pago, falhou, reembolsado)
  * Integração futura com gateway de pagamento

- Cancelamento e suspensão:
  * Usuário pode cancelar assinatura
  * Admin pode suspender assinatura
  * Período de carência antes de expirar

- Upgrade/Downgrade:
  * Usuário pode mudar de plano
  * Cálculo proporcional de valores
  * Aplicação imediata de novos limites


✅ 7. Sistema Administrativo (NOVO)

7.1. Funcionalidades do Admin:

- Gerenciamento de usuários:
  * Listar, criar, editar, desativar usuários
  * Verificar perfis de prestadores
  * Gerenciar permissões

- Gerenciamento de conteúdo:
  * CRUD de categorias e serviços
  * Moderar pedidos e propostas
  * Gerenciar reviews (aprovar/rejeitar)

- Gerenciamento de assinaturas:
  * Criar/editar planos
  * Visualizar assinaturas ativas
  * Gerenciar pagamentos
  * Suspender/cancelar assinaturas

- Gerenciamento de pagamentos:
  * Visualizar todos os pagamentos
  * Processar reembolsos
  * Gerar relatórios financeiros

- Estatísticas e relatórios:
  * Dashboard com métricas principais
  * Relatórios de uso da plataforma
  * Análise de receita
  * Usuários mais ativos

- Auditoria:
  * Log de todas as ações administrativas
  * Histórico de mudanças
  * Rastreamento de IP

7.2. Permissões Admin:

- Super Admin: Acesso total
- Content Moderator: Pode moderar conteúdo
- Support Admin: Pode gerenciar usuários e suporte
- Financial Admin: Pode gerenciar pagamentos e assinaturas


✅ 8. Rotas (REST recomendadas - EXPANDIDAS)

/auth/

POST /auth/register
POST /auth/login
POST /auth/refresh
POST /auth/logout
GET /auth/me
PATCH /auth/me
POST /auth/password/reset
POST /auth/password/reset/confirm

/services/

GET /categories/
GET /categories/{id}/
POST /categories/ (admin only)
PATCH /categories/{id}/ (admin only)
DELETE /categories/{id}/ (admin only)
GET /categories/{id}/services/
GET /services/
GET /services/{id}/
POST /services/ (admin only)
PATCH /services/{id}/ (admin only)
DELETE /services/{id}/ (admin only)

/orders/

GET /orders/ (filtros: status, service, client)
POST /orders/ (client only, verifica limite de assinatura)
GET /orders/{id}/
PATCH /orders/{id}/status/ (owner only)
DELETE /orders/{id}/ (owner only, apenas se PENDING)
GET /orders/{id}/proposals/

/proposals/

GET /proposals/ (filtros: order, provider, status)
POST /proposals/ (provider only, verifica limite de assinatura)
GET /proposals/{id}/
PATCH /proposals/{id}/accept (order owner only)
PATCH /proposals/{id}/decline (order owner only)
DELETE /proposals/{id}/ (owner only, apenas se PENDING)

/chat/

GET /chat/rooms/ (lista salas do usuário)
GET /chat/rooms/{id}/
POST /chat/rooms/ (cria sala para um pedido)
GET /chat/rooms/{id}/messages/
POST /chat/rooms/{id}/messages/
PATCH /chat/rooms/{id}/messages/{message_id}/read
GET /chat/rooms/{id}/unread-count/
WebSocket: /ws/chat/{room_id}/

/subscriptions/

GET /subscriptions/plans/
GET /subscriptions/plans/{id}/
POST /subscriptions/plans/ (admin only)
PATCH /subscriptions/plans/{id}/ (admin only)
GET /subscriptions/my-subscription/
POST /subscriptions/subscribe/ (escolher plano)
PATCH /subscriptions/my-subscription/cancel/
PATCH /subscriptions/my-subscription/reactivate/
GET /subscriptions/my-subscription/payments/
GET /subscriptions/my-subscription/usage/ (mostra uso atual vs limites)

/payments/ (pagamentos de serviços)

GET /payments/ (filtros: order, status)
POST /payments/ (criar pagamento - simulação)
GET /payments/{id}/
PATCH /payments/{id}/status/ (admin only)
POST /payments/{id}/refund/ (admin only)

/reviews/

GET /reviews/ (filtros: reviewed_user, order)
POST /orders/{id}/review (order owner only, após conclusão)
GET /reviews/{id}/
PATCH /reviews/{id}/ (owner only)
DELETE /reviews/{id}/ (owner only)

/admin/ (todos os endpoints requerem permissão admin)

GET /admin/dashboard/stats/
GET /admin/users/
GET /admin/users/{id}/
PATCH /admin/users/{id}/
POST /admin/users/{id}/suspend/
POST /admin/users/{id}/activate/
GET /admin/orders/
GET /admin/proposals/
GET /admin/payments/
GET /admin/subscriptions/
GET /admin/reviews/
GET /admin/audit-logs/


✅ 9. Sistema de Filas (Celery + Redis)

9.1. Configuração:

- Celery como broker de mensagens
- Redis como message broker e result backend
- Filas separadas por tipo de tarefa (emails, notificações, processamento pesado)
- Retry automático para tarefas que falharem
- Dead letter queue para tarefas que falharam múltiplas vezes

9.2. Filas de Email:

Jobs de email (fila: `emails`):
- Enviar email quando cliente cria pedido
- Enviar email quando prestador recebe proposta nova
- Enviar email de notificação de nova mensagem no chat (se usuário offline)
- Enviar email de boas-vindas ao registrar
- Enviar email de confirmação de pagamento
- Enviar email de vencimento de assinatura (7 dias antes, 1 dia antes)
- Enviar email de renovação de assinatura
- Enviar email de lembretes (pedidos pendentes, propostas expiradas)
- Enviar email de recuperação de senha
- Enviar email de notificações administrativas

9.3. Filas de Notificações Push (Firebase - Preparado para futuro):

Estrutura preparada para integração com Firebase Cloud Messaging (FCM):
- Fila: `push_notifications`
- Modelo: DeviceToken (armazenar tokens FCM dos dispositivos dos usuários)
- Jobs de notificação push:
  * Notificar quando cliente cria pedido
  * Notificar quando prestador recebe proposta nova
  * Notificar nova mensagem no chat
  * Notificar quando proposta é aceita/recusada
  * Notificar quando pedido muda de status
  * Notificar lembretes e alertas
  * Notificar sobre assinaturas (vencimento, renovação)

Configuração futura:
- Instalar `firebase-admin` SDK
- Configurar credenciais do Firebase no settings
- Criar serviço de notificações push
- Gerenciar tokens de dispositivos (registrar, atualizar, remover)
- Tratar erros de tokens inválidos/expirados

9.4. Outras Filas:

Fila de processamento pesado (`heavy_tasks`):
- Calcular ranking dos prestadores periodicamente (diário)
- Gerar relatórios administrativos (semanal/mensal)
- Processar uploads de arquivos grandes
- Gerar PDFs de propostas

Fila de manutenção (`maintenance`):
- Limpar propostas expiradas (tarefa periódica)
- Processar renovações de assinatura (diário)
- Resetar contadores mensais de assinaturas (primeiro dia do mês)
- Limpar tokens expirados
- Limpar sessões antigas
- Backup de dados

Fila de logs (`logging`):
- Gerar logs e histórico
- Auditoria de eventos
- Métricas e analytics

9.5. Monitoramento:

- Flower para monitorar Celery workers
- Logs de tarefas executadas
- Alertas para tarefas que falharam
- Métricas de performance das filas


✅ 10. Documentação da API (Swagger/OpenAPI)

10.1. Configuração:

- Usar `drf-yasg` ou `drf-spectacular` para gerar documentação Swagger/OpenAPI
- Documentação automática baseada nos serializers e viewsets
- Interface interativa para testar endpoints
- Documentação de schemas, parâmetros, respostas e códigos de erro

10.2. Endpoints de Documentação:

- `/swagger/` - Interface Swagger UI
- `/redoc/` - Interface ReDoc (alternativa)
- `/openapi.json` - Esquema OpenAPI em JSON
- `/openapi.yaml` - Esquema OpenAPI em YAML

10.3. Boas Práticas:

- Documentar todos os endpoints
- Incluir exemplos de requisições e respostas
- Documentar códigos de erro possíveis
- Adicionar descrições detalhadas nos serializers
- Incluir tags para organização
- Documentar autenticação necessária
- Adicionar exemplos de uso


✅ 11. Observabilidade e Monitoramento

11.1. Bibliotecas Recomendadas:

- **Sentry** (recomendado):
  * Monitoramento de erros e exceções em tempo real
  * Rastreamento de performance
  * Alertas automáticos
  * Integração com Django/Django REST Framework
  * Rastreamento de releases e deploys

- **Prometheus + Grafana** (opcional, para métricas avançadas):
  * Coleta de métricas customizadas
  * Dashboards personalizados
  * Alertas baseados em métricas

11.2. Métricas a Monitorar:

- Performance:
  * Tempo de resposta dos endpoints
  * Queries lentas no banco de dados
  * Uso de memória e CPU
  * Throughput de requisições

- Erros:
  * Taxa de erros por endpoint
  * Exceções não tratadas
  * Erros de validação
  * Erros de autenticação/autorização

- Negócio:
  * Número de usuários ativos
  * Pedidos criados/completados
  * Propostas enviadas/aceitas
  * Assinaturas ativas
  * Taxa de conversão

- Infraestrutura:
  * Status dos workers Celery
  * Uso de Redis
  * Espaço em disco
  * Conexões com banco de dados

11.3. Logging:

- Configurar logging estruturado (JSON)
- Níveis de log: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Logs de requisições HTTP (middleware)
- Logs de queries SQL (em desenvolvimento)
- Logs de tarefas Celery
- Rotação de logs

11.4. Health Checks:

- Endpoint `/health/` para verificar status da aplicação
- Endpoint `/health/db/` para verificar conexão com banco
- Endpoint `/health/redis/` para verificar conexão com Redis
- Endpoint `/health/celery/` para verificar status dos workers


✅ 12. Testes Automatizados

12.1. Estrutura de Testes:

- Usar `pytest` ou `unittest` (padrão do Django)
- Organizar testes por app (accounts/tests/, orders/tests/, etc.)
- Separar testes unitários, de integração e e2e

12.2. Testes Unitários:

- Testar modelos (validações, métodos, propriedades)
- Testar serializers (validação, transformação de dados)
- Testar permissões customizadas
- Testar utilitários e helpers
- Testar tasks do Celery (mock de dependências externas)
- Cobertura mínima recomendada: 80%

12.3. Testes de Integração:

- Testar endpoints da API (ViewSets)
- Testar fluxos completos (ex: criar pedido → receber proposta → aceitar)
- Testar autenticação e autorização
- Testar validações de limites de assinatura
- Testar soft delete
- Testar relacionamentos entre modelos

12.4. Testes End-to-End (E2E):

- Testar fluxos críticos do negócio:
  * Registro → Login → Criar pedido → Receber proposta → Aceitar → Pagar → Review
  * Assinatura → Upgrade → Cancelamento
  * Chat completo (criar sala → enviar mensagens → marcar como lida)
- Usar `pytest-django` com fixtures
- Mock de serviços externos (email, Firebase, gateways de pagamento)

12.5. Ferramentas e Bibliotecas:

- `pytest` - Framework de testes
- `pytest-django` - Integração com Django
- `pytest-cov` - Cobertura de código
- `factory-boy` - Factories para criar dados de teste
- `faker` - Dados fake para testes
- `freezegun` - Mock de datas/tempos
- `responses` - Mock de requisições HTTP
- `django-test-plus` - Helpers adicionais para testes Django

12.6. CI/CD:

- Executar testes automaticamente em cada commit/PR
- Verificar cobertura de código
- Executar linters (flake8, black, isort)
- Executar testes de segurança (bandit, safety)


✅ 13. Recursos Avançados (para quando você quiser evoluir)

- Pré-visualização de propostas com PDFs gerados (Celery)
- Pagamentos com Stripe / Asaas / Mercado Pago
- Cache com Redis (para categorias, serviços, rankings)
- Rate limiting (DRF throttling)
- Upload de arquivos para S3 ou storage local
- API de webhooks para integrações externas
- Sistema de cupons/descontos para assinaturas
- Analytics e tracking de eventos
- Sistema de tags para pedidos e serviços
- Busca avançada com Elasticsearch
- Sistema de favoritos (prestadores favoritos)
- Histórico de visualizações


✅ 14. Soft Delete (Exclusão Lógica)

14.1. Implementação:

- Todas as tabelas possuem campo `deleted_at` (DateTimeField, nullable)
- Quando `deleted_at` é NULL: registro está ativo
- Quando `deleted_at` tem valor: registro está deletado (mas permanece no banco)

14.2. Manager Customizado:

- Criar `SoftDeleteManager` que filtra automaticamente registros deletados
- Usar `objects` para queries normais (exclui deletados)
- Usar `all_objects` para incluir deletados quando necessário
- Usar `deleted_objects` para buscar apenas deletados

14.3. Métodos:

- `delete()`: Marca `deleted_at` com timestamp atual (não remove do banco)
- `hard_delete()`: Remove fisicamente do banco (usar com cuidado)
- `restore()`: Restaura registro deletado (define `deleted_at` como NULL)

14.4. Regras Especiais:

- Pagamentos e logs: Não devem ser deletados, apenas marcados (auditoria)
- Planos ativos: Não devem ser deletados, apenas desativados (`is_active=False`)
- Usuários: Soft delete mantém integridade referencial
- Relacionamentos: Verificar se registros relacionados estão deletados

14.5. Queries:

- Queries padrão automaticamente excluem registros deletados
- Admin pode ver registros deletados com filtro especial
- Relatórios podem incluir/excluir deletados conforme necessário


✅ 15. Validação de Dados e Formulários

15.1. Validação no Backend (Django REST Framework):

- Serializers com validação completa:
  * Validação de tipos de dados
  * Validação de campos obrigatórios
  * Validação de formatos (email, telefone, CPF/CNPJ)
  * Validação de ranges (valores mínimos/máximos)
  * Validação customizada com métodos `validate_<campo>()`
  * Validação de relacionamentos (FKs existentes)

- Validações específicas por modelo:
  * User: email único, senha forte, telefone válido
  * Order: budget_min < budget_max, deadline no futuro
  * Proposal: price > 0, estimated_days > 0, expires_at no futuro
  * Payment: amount > 0, payment_date não no passado
  * Review: rating entre 1-5, apenas uma review por order
  * Subscription: datas válidas, plan ativo

- Validação de permissões:
  * Verificar se usuário tem permissão para criar/editar/deletar
  * Verificar limites de assinatura antes de criar pedidos/propostas
  * Verificar se recursos pertencem ao usuário

15.2. Validação no Frontend (Recomendações):

- Validação em tempo real nos formulários (responsabilidade do frontend)
- Feedback visual de erros
- Prevenção de submissão duplicada
- Sanitização de inputs antes de enviar

15.3. Validação de Integridade:

- Constraints no banco de dados (unique, check)
- Transações atômicas para operações críticas
- Validação de estado antes de mudanças (ex: não aceitar proposta já aceita)


✅ 16. Considerações de Segurança

- Validação de dados em todos os endpoints (ver seção 15)
- Sanitização de inputs (XSS prevention)
- Rate limiting por IP e por usuário
- CORS configurado adequadamente
- HTTPS obrigatório em produção
- **Tokens JWT com expiração curta (15-30 min) e renovação automática** (ver seção 4.1)
- Refresh tokens com rotação
- **Hash de senhas SEMPRE com bcrypt** (ver seção 4.2)
- **Proteção contra SQL injection (ORM do Django)**:
  * Django ORM usa parameterized queries por padrão, prevenindo SQL injection
  * NUNCA usar `.raw()` ou `.extra()` com strings não sanitizadas
  * Se necessário usar SQL raw, sempre usar parâmetros nomeados
  * Validar e sanitizar todos os inputs antes de usar em queries
  * Usar apenas métodos seguros do ORM (filter, get, exclude, etc.)
  * Evitar concatenação de strings em queries
- Validação de permissões em todos os endpoints/viewsets
- Logs de segurança (tentativas de login falhadas)
- Backup criptografado de dados sensíveis
- Soft delete para manter integridade referencial e auditoria
- Validação de CSRF tokens (para endpoints que necessitam, se houver)
- Headers de segurança (X-Content-Type-Options, X-Frame-Options, etc.)
- Validação de tamanho de uploads
- Limite de requisições por endpoint (throttling)


✅ 17. Análise e Melhorias Implementadas

17.1. Problemas Identificados e Resolvidos:

- ❌ Chat mal estruturado → ✅ Sistema robusto com ChatRoom, status de leitura, tipos de mensagem
- ❌ Falta sistema de assinaturas → ✅ Sistema completo com planos, assinaturas e pagamentos
- ❌ Falta sistema administrativo → ✅ Sistema admin completo com auditoria
- ❌ Pagamentos mal definidos → ✅ Separação clara entre pagamentos de assinatura e serviços
- ❌ Rotas incompletas → ✅ Rotas expandidas com todos os endpoints necessários
- ❌ Falta controle de limites → ✅ Sistema de limites baseado em planos de assinatura
- ❌ Falta auditoria → ✅ Sistema de logs de ações administrativas
- ❌ Sem soft delete → ✅ Soft delete implementado em todas as tabelas
- ❌ Sistema de filas básico → ✅ Sistema completo com filas separadas e preparação para Firebase
- ❌ Validação não detalhada → ✅ Seção completa de validação de dados
- ❌ JWT sem renovação automática → ✅ Sistema de renovação automática de tokens
- ❌ Hash de senhas genérico → ✅ Especificado uso obrigatório de bcrypt
- ❌ Sem observabilidade → ✅ Sistema de observabilidade com Sentry implementado
- ❌ Sem documentação Swagger → ✅ Documentação Swagger/OpenAPI configurada
- ❌ Testes não detalhados → ✅ Estrutura completa de testes (unitários, integração, e2e)
- ❌ Menções a views/telas → ✅ Removido, projeto é API REST pura

17.2. Melhorias Adicionais Propostas:

- Sistema de notificações in-app além de email
- Dashboard para usuários verem suas estatísticas
- Sistema de badges/achievements para prestadores
- Filtros avançados de busca para pedidos e prestadores
- Sistema de denúncias para conteúdo inadequado
- Moderação automática de conteúdo (IA)
- Sistema de backup automático de dados
- API versionada (v1, v2)
- Integração com serviços de monitoramento avançado (Prometheus + Grafana)
- Testes de carga e performance
