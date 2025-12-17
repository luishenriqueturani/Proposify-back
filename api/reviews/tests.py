"""
Testes unitários para o app reviews.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
import time
from datetime import timedelta
from decimal import Decimal
from api.reviews.models import Review
from api.accounts.models import User, ClientProfile, ProviderProfile
from api.accounts.enums import UserType
from api.services.models import ServiceCategory, Service
from api.orders.models import Order
from api.orders.enums import OrderStatus


class ReviewModelTestCase(TestCase):
    """Testes unitários para o modelo Review."""

    def setUp(self):
        """Cria dados de teste."""
        # Cria usuário cliente
        self.client_user = User.objects.create_user(  # type: ignore[call-arg]
            email='client@example.com',
            first_name='Client',
            last_name='User',
            password='testpass123',
            user_type=UserType.CLIENT.value
        )
        self.client_profile = ClientProfile.objects.create(user=self.client_user)

        # Cria usuário prestador
        self.provider_user = User.objects.create_user(  # type: ignore[call-arg]
            email='provider@example.com',
            first_name='Provider',
            last_name='User',
            password='testpass123',
            user_type=UserType.PROVIDER.value
        )
        self.provider_profile = ProviderProfile.objects.create(user=self.provider_user)

        # Cria categoria e serviço
        self.category = ServiceCategory.objects.create(name='Desenvolvimento Web')
        self.service = Service.objects.create(
            category=self.category,
            name='Desenvolvimento de Site'
        )

        # Cria pedido
        self.future_deadline = timezone.now() + timedelta(days=30)
        self.order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Desenvolvimento de E-commerce',
            description='Preciso de um e-commerce completo',
            budget_min=Decimal('5000.00'),
            budget_max=Decimal('10000.00'),
            deadline=self.future_deadline,
            status=OrderStatus.COMPLETED.value
        )

    def test_create_review_with_minimal_fields(self):
        """Testa criação de avaliação com campos mínimos."""
        review = Review.objects.create(
            order=self.order,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=5
        )
        self.assertEqual(review.order, self.order)
        self.assertEqual(review.reviewer, self.client_user)
        self.assertEqual(review.reviewed_user, self.provider_user)
        self.assertEqual(review.rating, 5)
        self.assertIsNone(review.comment)
        self.assertIsNotNone(review.created_at)
        self.assertIsNone(review.deleted_at)

    def test_create_review_with_all_fields(self):
        """Testa criação de avaliação com todos os campos."""
        review = Review.objects.create(
            order=self.order,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=4,
            comment='Excelente trabalho! Muito profissional.'
        )
        self.assertEqual(review.order, self.order)
        self.assertEqual(review.reviewer, self.client_user)
        self.assertEqual(review.reviewed_user, self.provider_user)
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.comment, 'Excelente trabalho! Muito profissional.')
        self.assertIsNotNone(review.created_at)
        self.assertIsNotNone(review.updated_at)
        self.assertIsNone(review.deleted_at)

    def test_order_is_required(self):
        """Testa que order é obrigatório."""
        review = Review(
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=5
        )
        with self.assertRaises(ValidationError):
            review.full_clean()

    def test_reviewer_is_required(self):
        """Testa que reviewer é obrigatório."""
        # Testa que não é possível criar review sem reviewer
        # Como clean() precisa de reviewer, testamos que o campo é obrigatório no banco
        review = Review(
            order=self.order,
            reviewed_user=self.provider_user,
            rating=5
        )
        # Tentar salvar sem reviewer deve falhar
        with self.assertRaises((ValidationError, IntegrityError, AttributeError)):
            review.save()

    def test_reviewed_user_is_required(self):
        """Testa que reviewed_user é obrigatório."""
        # Testa que não é possível criar review sem reviewed_user
        # Como clean() precisa de reviewed_user, testamos que o campo é obrigatório no banco
        review = Review(
            order=self.order,
            reviewer=self.client_user,
            rating=5
        )
        # Tentar salvar sem reviewed_user deve falhar
        with self.assertRaises((ValidationError, IntegrityError, AttributeError)):
            review.save()

    def test_rating_is_required(self):
        """Testa que rating é obrigatório."""
        review = Review(
            order=self.order,
            reviewer=self.client_user,
            reviewed_user=self.provider_user
        )
        with self.assertRaises(ValidationError):
            review.full_clean()

    def test_rating_minimum_value_is_1(self):
        """Testa que rating não pode ser menor que 1."""
        review = Review(
            order=self.order,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=0
        )
        with self.assertRaises(ValidationError) as context:
            review.full_clean()
        self.assertIn('rating', str(context.exception).lower())

    def test_rating_maximum_value_is_5(self):
        """Testa que rating não pode ser maior que 5."""
        review = Review(
            order=self.order,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=6
        )
        with self.assertRaises(ValidationError) as context:
            review.full_clean()
        self.assertIn('rating', str(context.exception).lower())

    def test_rating_accepts_values_from_1_to_5(self):
        """Testa que rating aceita valores de 1 a 5."""
        # Cria diferentes pedidos para cada rating para evitar unique constraint
        for rating in range(1, 6):
            order = Order.objects.create(
                client=self.client_profile,
                service=self.service,
                title=f'Pedido {rating}',
                description=f'Pedido para teste de rating {rating}',
                budget_min=Decimal('1000.00'),
                budget_max=Decimal('2000.00'),
                deadline=self.future_deadline,
                status=OrderStatus.COMPLETED.value
            )
            review = Review.objects.create(
                order=order,
                reviewer=self.client_user,
                reviewed_user=self.provider_user,
                rating=rating
            )
            self.assertEqual(review.rating, rating)

    def test_rating_validation_at_boundary_values(self):
        """Testa validação de rating nos valores de limite."""
        # Rating = 1 (mínimo válido)
        review1 = Review.objects.create(
            order=self.order,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=1
        )
        self.assertEqual(review1.rating, 1)

        # Rating = 5 (máximo válido) - precisa de outro pedido ou outro reviewer
        # Cria outro pedido para evitar unique constraint
        order2 = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Segundo Pedido',
            description='Outro pedido',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=self.future_deadline,
            status=OrderStatus.COMPLETED.value
        )

        review2 = Review.objects.create(
            order=order2,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=5
        )
        self.assertEqual(review2.rating, 5)

    def test_unique_constraint_order_reviewer(self):
        """Testa que unique constraint (order, reviewer) funciona."""
        # Cria primeira avaliação
        Review.objects.create(
            order=self.order,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=5
        )

        # Tentar criar outra avaliação com mesmo order e reviewer deve falhar
        # Pode levantar ValidationError (via full_clean) ou IntegrityError (no banco)
        with self.assertRaises((ValidationError, IntegrityError)):
            Review.objects.create(
                order=self.order,
                reviewer=self.client_user,
                reviewed_user=self.provider_user,
                rating=4
            )

    def test_unique_constraint_allows_different_reviewers(self):
        """Testa que unique constraint permite diferentes reviewers para o mesmo pedido."""
        # Cria outro usuário cliente
        client_user2 = User.objects.create_user(  # type: ignore[call-arg]
            email='client2@example.com',
            first_name='Client',
            last_name='User2',
            password='testpass123',
            user_type=UserType.CLIENT.value
        )

        # Primeira avaliação
        review1 = Review.objects.create(
            order=self.order,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=5
        )

        # Segunda avaliação com reviewer diferente (deve funcionar)
        review2 = Review.objects.create(
            order=self.order,
            reviewer=client_user2,
            reviewed_user=self.provider_user,
            rating=4
        )

        self.assertNotEqual(review1.reviewer, review2.reviewer)
        self.assertEqual(review1.order, review2.order)

    def test_unique_constraint_allows_same_reviewer_different_orders(self):
        """Testa que unique constraint permite mesmo reviewer em pedidos diferentes."""
        # Cria outro pedido
        order2 = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Segundo Pedido',
            description='Outro pedido',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=self.future_deadline,
            status=OrderStatus.COMPLETED.value
        )

        # Primeira avaliação
        review1 = Review.objects.create(
            order=self.order,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=5
        )

        # Segunda avaliação com mesmo reviewer mas pedido diferente (deve funcionar)
        review2 = Review.objects.create(
            order=order2,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=4
        )

        self.assertEqual(review1.reviewer, review2.reviewer)
        self.assertNotEqual(review1.order, review2.order)

    def test_reviewer_cannot_review_self(self):
        """Testa que reviewer não pode se avaliar."""
        review = Review(
            order=self.order,
            reviewer=self.client_user,
            reviewed_user=self.client_user,  # Mesmo usuário
            rating=5
        )
        with self.assertRaises(ValidationError) as context:
            review.full_clean()
        self.assertIn('não pode se avaliar', str(context.exception))

    def test_reviewer_cannot_review_self_on_save(self):
        """Testa que save() valida que reviewer não pode se avaliar."""
        review = Review(
            order=self.order,
            reviewer=self.client_user,
            reviewed_user=self.client_user,  # Mesmo usuário
            rating=5
        )
        with self.assertRaises(ValidationError):
            review.save()

    def test_comment_is_optional(self):
        """Testa que comment é opcional."""
        # Sem comment
        review1 = Review.objects.create(
            order=self.order,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=5,
            comment=None
        )
        self.assertIsNone(review1.comment)

        # Com comment
        review2 = Review.objects.create(
            order=self.order,
            reviewer=self.provider_user,
            reviewed_user=self.client_user,
            rating=4,
            comment='Cliente muito comunicativo e claro nos requisitos.'
        )
        self.assertIsNotNone(review2.comment)
        self.assertEqual(review2.comment, 'Cliente muito comunicativo e claro nos requisitos.')

    def test_bidirectional_reviews(self):
        """Testa que cliente e prestador podem se avaliar mutuamente."""
        # Cliente avalia prestador
        review1 = Review.objects.create(
            order=self.order,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=5,
            comment='Excelente trabalho!'
        )

        # Prestador avalia cliente
        review2 = Review.objects.create(
            order=self.order,
            reviewer=self.provider_user,
            reviewed_user=self.client_user,
            rating=4,
            comment='Cliente muito profissional.'
        )

        self.assertEqual(review1.reviewer, self.client_user)
        self.assertEqual(review1.reviewed_user, self.provider_user)
        self.assertEqual(review2.reviewer, self.provider_user)
        self.assertEqual(review2.reviewed_user, self.client_user)
        self.assertEqual(review1.order, review2.order)

    def test_order_foreign_key_relationship(self):
        """Testa relacionamento ForeignKey com Order."""
        review1 = Review.objects.create(
            order=self.order,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=5
        )

        # Cria outro pedido
        order2 = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Segundo Pedido',
            description='Outro pedido',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=self.future_deadline,
            status=OrderStatus.COMPLETED.value
        )

        review2 = Review.objects.create(
            order=order2,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=4
        )

        # Verifica relacionamento direto
        self.assertEqual(review1.order, self.order)
        self.assertEqual(review2.order, order2)

        # Verifica relacionamento reverso
        reviews = self.order.reviews.all()
        self.assertEqual(reviews.count(), 1)
        self.assertIn(review1, reviews)

    def test_reviewer_foreign_key_relationship(self):
        """Testa relacionamento ForeignKey com User (reviewer)."""
        review1 = Review.objects.create(
            order=self.order,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=5
        )

        # Cria outro pedido
        order2 = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Segundo Pedido',
            description='Outro pedido',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=self.future_deadline,
            status=OrderStatus.COMPLETED.value
        )

        review2 = Review.objects.create(
            order=order2,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=4
        )

        # Verifica relacionamento direto
        self.assertEqual(review1.reviewer, self.client_user)
        self.assertEqual(review2.reviewer, self.client_user)

        # Verifica relacionamento reverso
        reviews = self.client_user.reviews_given.all()
        self.assertEqual(reviews.count(), 2)
        self.assertIn(review1, reviews)
        self.assertIn(review2, reviews)

    def test_reviewed_user_foreign_key_relationship(self):
        """Testa relacionamento ForeignKey com User (reviewed_user)."""
        review1 = Review.objects.create(
            order=self.order,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=5
        )

        # Cria outro pedido
        order2 = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Segundo Pedido',
            description='Outro pedido',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=self.future_deadline,
            status=OrderStatus.COMPLETED.value
        )

        review2 = Review.objects.create(
            order=order2,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=4
        )

        # Verifica relacionamento direto
        self.assertEqual(review1.reviewed_user, self.provider_user)
        self.assertEqual(review2.reviewed_user, self.provider_user)

        # Verifica relacionamento reverso
        reviews = self.provider_user.reviews_received.all()
        self.assertEqual(reviews.count(), 2)
        self.assertIn(review1, reviews)
        self.assertIn(review2, reviews)

    def test_str_representation(self):
        """Testa a representação string do modelo."""
        review = Review.objects.create(
            order=self.order,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=5
        )
        expected = f"Avaliação #{review.id} - {self.client_user.email} avaliou {self.provider_user.email} (5/5)"
        self.assertEqual(str(review), expected)

    def test_created_at_auto_now_add(self):
        """Testa que created_at é preenchido automaticamente."""
        before = timezone.now()
        review = Review.objects.create(
            order=self.order,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=5
        )
        after = timezone.now()

        self.assertIsNotNone(review.created_at)
        self.assertGreaterEqual(review.created_at, before)
        self.assertLessEqual(review.created_at, after)

    def test_updated_at_auto_now(self):
        """Testa que updated_at é atualizado automaticamente."""
        review = Review.objects.create(
            order=self.order,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=5
        )
        original_updated_at = review.updated_at

        # Aguarda um pouco para garantir diferença de tempo
        time.sleep(0.01)

        review.comment = 'Comentário atualizado'
        review.save()

        self.assertGreater(review.updated_at, original_updated_at)

    def test_soft_delete_functionality(self):
        """Testa funcionalidade de soft delete."""
        review = Review.objects.create(
            order=self.order,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=5
        )

        # Avaliação está ativa
        self.assertIsNone(review.deleted_at)
        self.assertTrue(review.is_alive)
        self.assertFalse(review.is_deleted)
        self.assertEqual(Review.objects.count(), 1)

        # Deleta (soft delete)
        review.delete()
        review.refresh_from_db()

        # Avaliação está deletada
        self.assertIsNotNone(review.deleted_at)
        self.assertFalse(review.is_alive)
        self.assertTrue(review.is_deleted)
        self.assertEqual(Review.objects.count(), 0)
        self.assertEqual(Review.all_objects.count(), 1)
        self.assertEqual(Review.deleted_objects.count(), 1)

        # Restaura
        review.restore()
        review.refresh_from_db()

        # Avaliação está ativa novamente
        self.assertIsNone(review.deleted_at)
        self.assertTrue(review.is_alive)
        self.assertFalse(review.is_deleted)
        self.assertEqual(Review.objects.count(), 1)

    def test_ordering_by_created_at_desc(self):
        """Testa que ordenação padrão é por created_at descendente."""
        review1 = Review.objects.create(
            order=self.order,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=5
        )

        time.sleep(0.01)

        review2 = Review.objects.create(
            order=self.order,
            reviewer=self.provider_user,
            reviewed_user=self.client_user,
            rating=4
        )

        reviews = list(Review.objects.all())

        # review2 é mais recente, deve aparecer primeiro
        self.assertEqual(reviews[0], review2)
        self.assertEqual(reviews[1], review1)

    def test_indexes_exist(self):
        """Testa que os índices foram criados corretamente."""
        review = Review.objects.create(
            order=self.order,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=5
        )

        # Testa queries que usam os índices (verifica que não há erros)
        Review.objects.filter(order=self.order).first()
        Review.objects.filter(reviewer=self.client_user).first()
        Review.objects.filter(reviewed_user=self.provider_user).first()
        Review.objects.filter(rating=5).first()
        Review.objects.filter(deleted_at__isnull=True).first()

        # Verifica que os índices estão definidos no Meta
        index_names = [idx.name for idx in Review._meta.indexes]
        self.assertIn('review_order_idx', index_names)
        self.assertIn('review_reviewer_idx', index_names)
        self.assertIn('review_reviewed_user_idx', index_names)
        self.assertIn('review_rating_idx', index_names)
        self.assertIn('review_deleted_at_idx', index_names)

    def test_unique_constraint_name(self):
        """Testa que o nome da constraint única está correto."""
        constraint_names = [constraint.name for constraint in Review._meta.constraints]
        self.assertIn('unique_review_order_reviewer', constraint_names)

    def test_cascade_delete_when_order_hard_deleted(self):
        """Testa que avaliações são deletadas quando pedido é hard deleted."""
        review = Review.objects.create(
            order=self.order,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=5
        )
        review_id = review.id

        # Hard delete do pedido
        self.order.hard_delete()

        # A avaliação também deve ser deletada (CASCADE)
        self.assertFalse(Review.all_objects.filter(id=review_id).exists())

    def test_cascade_delete_when_reviewer_hard_deleted(self):
        """Testa que avaliações são deletadas quando avaliador é hard deleted."""
        review = Review.objects.create(
            order=self.order,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=5
        )
        review_id = review.id

        # Hard delete do avaliador
        self.client_user.hard_delete()

        # A avaliação também deve ser deletada (CASCADE)
        self.assertFalse(Review.all_objects.filter(id=review_id).exists())

    def test_cascade_delete_when_reviewed_user_hard_deleted(self):
        """Testa que avaliações são deletadas quando avaliado é hard deleted."""
        review = Review.objects.create(
            order=self.order,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=5
        )
        review_id = review.id

        # Hard delete do avaliado
        self.provider_user.hard_delete()

        # A avaliação também deve ser deletada (CASCADE)
        self.assertFalse(Review.all_objects.filter(id=review_id).exists())

    def test_multiple_reviews_for_same_order_different_reviewers(self):
        """Testa criação de múltiplas avaliações para o mesmo pedido com reviewers diferentes."""
        # Cliente avalia prestador
        review1 = Review.objects.create(
            order=self.order,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=5
        )

        # Prestador avalia cliente
        review2 = Review.objects.create(
            order=self.order,
            reviewer=self.provider_user,
            reviewed_user=self.client_user,
            rating=4
        )

        reviews = self.order.reviews.all()
        self.assertEqual(reviews.count(), 2)
        self.assertIn(review1, reviews)
        self.assertIn(review2, reviews)
