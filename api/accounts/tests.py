"""
Testes unitários para o app accounts.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal
import time
import uuid
from api.accounts.models import User, ProviderProfile, ClientProfile
from api.accounts.enums import UserType
from api.accounts.serializers import (
    UserRegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)


class UserModelTestCase(TestCase):
    """Testes unitários para o modelo User."""

    def setUp(self):
        """Cria dados de teste."""
        self.user_data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpass123',
        }

    def test_create_user_with_minimal_fields(self):
        """Testa criação de usuário com campos mínimos."""
        user = User.objects.create_user(**self.user_data)
        
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.user_type, UserType.CLIENT.value)
        self.assertIsNone(user.phone)
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.updated_at)
        self.assertIsNone(user.deleted_at)
        self.assertTrue(user.is_client)
        self.assertFalse(user.is_provider)
        self.assertFalse(user.is_admin_user)

    def test_create_user_with_all_fields(self):
        """Testa criação de usuário com todos os campos."""
        user_data = {
            **self.user_data,
            'phone': '+5511999999999',
            'user_type': UserType.PROVIDER.value,
        }
        user = User.objects.create_user(**user_data)
        
        self.assertEqual(user.phone, '+5511999999999')
        self.assertEqual(user.user_type, UserType.PROVIDER.value)
        self.assertTrue(user.is_provider)
        self.assertFalse(user.is_client)

    def test_email_is_unique(self):
        """Testa que email deve ser único."""
        User.objects.create_user(**self.user_data)
        
        with self.assertRaises(IntegrityError):
            User.objects.create_user(**self.user_data)

    def test_email_is_required(self):
        """Testa que email é obrigatório."""
        # Tenta criar usuário sem email (passando None)
        with self.assertRaises(ValueError):
            User.objects.create_user(email=None, password='testpass123')
        
        # Tenta criar usuário sem passar email
        with self.assertRaises(TypeError):
            User.objects.create_user(password='testpass123')

    def test_username_field_is_email(self):
        """Testa que USERNAME_FIELD é email."""
        self.assertEqual(User.USERNAME_FIELD, 'email')

    def test_required_fields(self):
        """Testa que REQUIRED_FIELDS contém first_name e last_name."""
        self.assertIn('first_name', User.REQUIRED_FIELDS)
        self.assertIn('last_name', User.REQUIRED_FIELDS)

    def test_user_type_default_is_client(self):
        """Testa que user_type padrão é CLIENT."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.user_type, UserType.CLIENT.value)

    def test_user_type_choices(self):
        """Testa que user_type aceita apenas valores válidos."""
        # CLIENT
        user = User.objects.create_user(**self.user_data)
        user.user_type = UserType.CLIENT.value
        user.save()
        self.assertEqual(user.user_type, UserType.CLIENT.value)
        
        # PROVIDER
        user.user_type = UserType.PROVIDER.value
        user.save()
        self.assertEqual(user.user_type, UserType.PROVIDER.value)
        
        # ADMIN
        user.user_type = UserType.ADMIN.value
        user.save()
        self.assertEqual(user.user_type, UserType.ADMIN.value)

    def test_phone_is_optional(self):
        """Testa que phone é opcional."""
        user = User.objects.create_user(**self.user_data)
        self.assertIsNone(user.phone)
        
        user.phone = '+5511999999999'
        user.save()
        self.assertEqual(user.phone, '+5511999999999')

    def test_is_client_property(self):
        """Testa a propriedade is_client."""
        user = User.objects.create_user(**self.user_data)
        self.assertTrue(user.is_client)
        
        user.user_type = UserType.PROVIDER.value
        user.save()
        self.assertFalse(user.is_client)
        
        user.user_type = UserType.ADMIN.value
        user.save()
        self.assertFalse(user.is_client)

    def test_is_provider_property(self):
        """Testa a propriedade is_provider."""
        user = User.objects.create_user(**self.user_data)
        self.assertFalse(user.is_provider)
        
        user.user_type = UserType.PROVIDER.value
        user.save()
        self.assertTrue(user.is_provider)
        
        user.user_type = UserType.ADMIN.value
        user.save()
        self.assertFalse(user.is_provider)

    def test_is_admin_user_property(self):
        """Testa a propriedade is_admin_user."""
        # Usuário comum não é admin
        user = User.objects.create_user(**self.user_data)
        self.assertFalse(user.is_admin_user)
        
        # Usuário com user_type ADMIN é admin
        user.user_type = UserType.ADMIN.value
        user.save()
        self.assertTrue(user.is_admin_user)
        
        # Usuário com is_staff=True é admin
        user.user_type = UserType.CLIENT.value
        user.is_staff = True
        user.save()
        self.assertTrue(user.is_admin_user)
        
        # Usuário com is_superuser=True é admin
        user.is_staff = False
        user.is_superuser = True
        user.save()
        self.assertTrue(user.is_admin_user)

    def test_str_representation(self):
        """Testa a representação string do modelo."""
        user = User.objects.create_user(**self.user_data)
        expected = f"{user.email} ({UserType.CLIENT.label})"
        self.assertEqual(str(user), expected)
        
        user.user_type = UserType.PROVIDER.value
        user.save()
        expected = f"{user.email} ({UserType.PROVIDER.label})"
        self.assertEqual(str(user), expected)

    def test_created_at_auto_now_add(self):
        """Testa que created_at é preenchido automaticamente."""
        before = timezone.now()
        user = User.objects.create_user(**self.user_data)
        after = timezone.now()
        
        self.assertIsNotNone(user.created_at)
        self.assertGreaterEqual(user.created_at, before)
        self.assertLessEqual(user.created_at, after)

    def test_updated_at_auto_now(self):
        """Testa que updated_at é atualizado automaticamente."""
        user = User.objects.create_user(**self.user_data)
        original_updated_at = user.updated_at
        
        # Aguarda um pouco para garantir diferença de tempo
        import time
        time.sleep(0.01)
        
        user.first_name = 'Updated'
        user.save()
        
        self.assertGreater(user.updated_at, original_updated_at)

    def test_soft_delete_functionality(self):
        """Testa funcionalidade de soft delete."""
        user = User.objects.create_user(**self.user_data)
        user_id = user.id
        
        # Usuário está ativo
        self.assertIsNone(user.deleted_at)
        self.assertTrue(user.is_alive)
        self.assertFalse(user.is_deleted)
        self.assertEqual(User.objects.count(), 1)
        
        # Deleta (soft delete)
        user.delete()
        user.refresh_from_db()
        
        # Usuário está deletado
        self.assertIsNotNone(user.deleted_at)
        self.assertFalse(user.is_alive)
        self.assertTrue(user.is_deleted)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(User.all_objects.count(), 1)
        self.assertEqual(User.deleted_objects.count(), 1)
        
        # Restaura
        user.restore()
        user.refresh_from_db()
        
        # Usuário está ativo novamente
        self.assertIsNone(user.deleted_at)
        self.assertTrue(user.is_alive)
        self.assertFalse(user.is_deleted)
        self.assertEqual(User.objects.count(), 1)

    def test_ordering_by_created_at_desc(self):
        """Testa que ordenação padrão é por created_at descendente."""
        user1 = User.objects.create_user(
            email='user1@example.com',
            first_name='User',
            last_name='One',
            password='pass123'
        )
        import time
        time.sleep(0.01)
        
        user2 = User.objects.create_user(
            email='user2@example.com',
            first_name='User',
            last_name='Two',
            password='pass123'
        )
        
        users = list(User.objects.all())
        self.assertEqual(users[0], user2)  # Mais recente primeiro
        self.assertEqual(users[1], user1)

    def test_indexes_exist(self):
        """Testa que os índices foram criados corretamente."""
        # Cria um usuário para testar
        user = User.objects.create_user(**self.user_data)
        
        # Testa queries que usam os índices (verifica que não há erros)
        # Os índices são criados automaticamente pelo Django
        User.objects.filter(email=user.email).first()
        User.objects.filter(user_type=UserType.CLIENT.value).first()
        User.objects.filter(deleted_at__isnull=True).first()
        
        # Verifica que os índices estão definidos no Meta
        self.assertIn('user_email_idx', [idx.name for idx in User._meta.indexes])
        self.assertIn('user_type_idx', [idx.name for idx in User._meta.indexes])
        self.assertIn('user_deleted_at_idx', [idx.name for idx in User._meta.indexes])

    def test_create_superuser(self):
        """Testa criação de superusuário."""
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            password='admin123'
        )
        
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_admin_user)


class ProviderProfileModelTestCase(TestCase):
    """Testes unitários para o modelo ProviderProfile."""

    def setUp(self):
        """Cria dados de teste."""
        self.user = User.objects.create_user(
            email='provider@example.com',
            first_name='Provider',
            last_name='User',
            password='testpass123',
            user_type=UserType.PROVIDER.value
        )

    def test_create_provider_profile_with_minimal_fields(self):
        """Testa criação de perfil de prestador com campos mínimos."""
        profile = ProviderProfile.objects.create(user=self.user)
        
        self.assertEqual(profile.user, self.user)
        self.assertIsNone(profile.bio)
        self.assertEqual(profile.rating_avg, Decimal('0.00'))
        self.assertEqual(profile.total_reviews, 0)
        self.assertEqual(profile.total_orders_completed, 0)
        self.assertFalse(profile.is_verified)
        self.assertIsNotNone(profile.created_at)
        self.assertIsNotNone(profile.updated_at)
        self.assertIsNone(profile.deleted_at)

    def test_create_provider_profile_with_all_fields(self):
        """Testa criação de perfil de prestador com todos os campos."""
        profile = ProviderProfile.objects.create(
            user=self.user,
            bio='Prestador experiente em desenvolvimento web',
            rating_avg=Decimal('4.50'),
            total_reviews=10,
            total_orders_completed=25,
            is_verified=True
        )
        
        self.assertEqual(profile.bio, 'Prestador experiente em desenvolvimento web')
        self.assertEqual(profile.rating_avg, Decimal('4.50'))
        self.assertEqual(profile.total_reviews, 10)
        self.assertEqual(profile.total_orders_completed, 25)
        self.assertTrue(profile.is_verified)

    def test_one_to_one_relationship(self):
        """Testa que o relacionamento OneToOne funciona corretamente."""
        profile = ProviderProfile.objects.create(user=self.user)
        
        # Acessa o perfil através do relacionamento reverso
        self.assertEqual(self.user.provider_profile, profile)
        
        # Um User só pode ter um ProviderProfile
        with self.assertRaises(IntegrityError):
            ProviderProfile.objects.create(user=self.user)

    def test_bio_is_optional(self):
        """Testa que bio é opcional."""
        profile1 = ProviderProfile.objects.create(user=self.user)
        self.assertIsNone(profile1.bio)
        
        profile2 = ProviderProfile.objects.create(
            user=User.objects.create_user(
                email='provider2@example.com',
                first_name='Provider',
                last_name='Two',
                password='testpass123',
                user_type=UserType.PROVIDER.value
            ),
            bio='Biografia do prestador'
        )
        self.assertEqual(profile2.bio, 'Biografia do prestador')

    def test_rating_avg_default(self):
        """Testa que rating_avg padrão é 0.00."""
        profile = ProviderProfile.objects.create(user=self.user)
        self.assertEqual(profile.rating_avg, Decimal('0.00'))

    def test_total_reviews_default(self):
        """Testa que total_reviews padrão é 0."""
        profile = ProviderProfile.objects.create(user=self.user)
        self.assertEqual(profile.total_reviews, 0)

    def test_total_orders_completed_default(self):
        """Testa que total_orders_completed padrão é 0."""
        profile = ProviderProfile.objects.create(user=self.user)
        self.assertEqual(profile.total_orders_completed, 0)

    def test_is_verified_default(self):
        """Testa que is_verified padrão é False."""
        profile = ProviderProfile.objects.create(user=self.user)
        self.assertFalse(profile.is_verified)

    def test_rating_avg_range(self):
        """Testa que rating_avg aceita valores de 0.00 a 5.00."""
        profile = ProviderProfile.objects.create(user=self.user)
        
        # Testa valores válidos
        profile.rating_avg = Decimal('0.00')
        profile.save()
        self.assertEqual(profile.rating_avg, Decimal('0.00'))
        
        profile.rating_avg = Decimal('5.00')
        profile.save()
        self.assertEqual(profile.rating_avg, Decimal('5.00'))
        
        profile.rating_avg = Decimal('3.75')
        profile.save()
        self.assertEqual(profile.rating_avg, Decimal('3.75'))

    def test_total_reviews_positive(self):
        """Testa que total_reviews aceita apenas valores positivos."""
        profile = ProviderProfile.objects.create(user=self.user)
        
        profile.total_reviews = 10
        profile.save()
        self.assertEqual(profile.total_reviews, 10)
        
        # PositiveIntegerField não aceita valores negativos
        with self.assertRaises(ValidationError):
            profile.total_reviews = -1
            profile.full_clean()

    def test_total_orders_completed_positive(self):
        """Testa que total_orders_completed aceita apenas valores positivos."""
        profile = ProviderProfile.objects.create(user=self.user)
        
        profile.total_orders_completed = 5
        profile.save()
        self.assertEqual(profile.total_orders_completed, 5)
        
        # PositiveIntegerField não aceita valores negativos
        with self.assertRaises(ValidationError):
            profile.total_orders_completed = -1
            profile.full_clean()

    def test_str_representation(self):
        """Testa a representação string do modelo."""
        profile = ProviderProfile.objects.create(user=self.user)
        expected = f"Perfil de {self.user.email}"
        self.assertEqual(str(profile), expected)

    def test_created_at_auto_now_add(self):
        """Testa que created_at é preenchido automaticamente."""
        before = timezone.now()
        profile = ProviderProfile.objects.create(user=self.user)
        after = timezone.now()
        
        self.assertIsNotNone(profile.created_at)
        self.assertGreaterEqual(profile.created_at, before)
        self.assertLessEqual(profile.created_at, after)

    def test_updated_at_auto_now(self):
        """Testa que updated_at é atualizado automaticamente."""
        profile = ProviderProfile.objects.create(user=self.user)
        original_updated_at = profile.updated_at
        
        # Aguarda um pouco para garantir diferença de tempo
        time.sleep(0.01)
        
        profile.bio = 'Biografia atualizada'
        profile.save()
        
        self.assertGreater(profile.updated_at, original_updated_at)

    def test_soft_delete_functionality(self):
        """Testa funcionalidade de soft delete."""
        profile = ProviderProfile.objects.create(user=self.user)
        profile_id = profile.id
        
        # Perfil está ativo
        self.assertIsNone(profile.deleted_at)
        self.assertTrue(profile.is_alive)
        self.assertFalse(profile.is_deleted)
        self.assertEqual(ProviderProfile.objects.count(), 1)
        
        # Deleta (soft delete)
        profile.delete()
        profile.refresh_from_db()
        
        # Perfil está deletado
        self.assertIsNotNone(profile.deleted_at)
        self.assertFalse(profile.is_alive)
        self.assertTrue(profile.is_deleted)
        self.assertEqual(ProviderProfile.objects.count(), 0)
        self.assertEqual(ProviderProfile.all_objects.count(), 1)
        self.assertEqual(ProviderProfile.deleted_objects.count(), 1)
        
        # Restaura
        profile.restore()
        profile.refresh_from_db()
        
        # Perfil está ativo novamente
        self.assertIsNone(profile.deleted_at)
        self.assertTrue(profile.is_alive)
        self.assertFalse(profile.is_deleted)
        self.assertEqual(ProviderProfile.objects.count(), 1)

    def test_ordering_by_rating_and_orders(self):
        """Testa que ordenação padrão é por rating_avg e total_orders_completed descendente."""
        # Cria perfis com diferentes ratings e orders
        user1 = User.objects.create_user(
            email='provider1@example.com',
            first_name='Provider',
            last_name='One',
            password='pass123',
            user_type=UserType.PROVIDER.value
        )
        profile1 = ProviderProfile.objects.create(
            user=user1,
            rating_avg=Decimal('4.00'),
            total_orders_completed=10
        )
        
        time.sleep(0.01)
        
        user2 = User.objects.create_user(
            email='provider2@example.com',
            first_name='Provider',
            last_name='Two',
            password='pass123',
            user_type=UserType.PROVIDER.value
        )
        profile2 = ProviderProfile.objects.create(
            user=user2,
            rating_avg=Decimal('5.00'),
            total_orders_completed=5
        )
        
        time.sleep(0.01)
        
        user3 = User.objects.create_user(
            email='provider3@example.com',
            first_name='Provider',
            last_name='Three',
            password='pass123',
            user_type=UserType.PROVIDER.value
        )
        profile3 = ProviderProfile.objects.create(
            user=user3,
            rating_avg=Decimal('4.00'),
            total_orders_completed=15
        )
        
        profiles = list(ProviderProfile.objects.all())
        
        # profile2 tem maior rating (5.00)
        self.assertEqual(profiles[0], profile2)
        
        # profile3 tem mesmo rating que profile1 (4.00) mas mais orders (15 > 10)
        self.assertEqual(profiles[1], profile3)
        self.assertEqual(profiles[2], profile1)

    def test_indexes_exist(self):
        """Testa que os índices foram criados corretamente."""
        profile = ProviderProfile.objects.create(user=self.user)
        
        # Testa queries que usam os índices (verifica que não há erros)
        ProviderProfile.objects.filter(rating_avg=Decimal('0.00')).first()
        ProviderProfile.objects.filter(is_verified=False).first()
        ProviderProfile.objects.filter(deleted_at__isnull=True).first()
        
        # Verifica que os índices estão definidos no Meta
        self.assertIn('provider_rating_avg_idx', [idx.name for idx in ProviderProfile._meta.indexes])
        self.assertIn('provider_is_verified_idx', [idx.name for idx in ProviderProfile._meta.indexes])
        self.assertIn('provider_deleted_at_idx', [idx.name for idx in ProviderProfile._meta.indexes])

    def test_update_rating_method_exists(self):
        """Testa que o método update_rating existe (mesmo que ainda não implementado)."""
        profile = ProviderProfile.objects.create(user=self.user)
        
        # O método existe e pode ser chamado (retorna None por enquanto)
        result = profile.update_rating()
        self.assertIsNone(result)

    def test_user_relationship(self):
        """Testa que o relacionamento com User funciona corretamente."""
        profile = ProviderProfile.objects.create(user=self.user)
        
        # Verifica que o perfil está associado ao usuário correto
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.user.email, 'provider@example.com')
        
        # Verifica que o usuário pode acessar o perfil
        self.assertEqual(self.user.provider_profile, profile)
        
        # Verifica que o usuário é do tipo PROVIDER
        self.assertTrue(self.user.is_provider)


class ClientProfileModelTestCase(TestCase):
    """Testes unitários para o modelo ClientProfile."""

    def setUp(self):
        """Cria dados de teste."""
        self.user = User.objects.create_user(
            email='client@example.com',
            first_name='Client',
            last_name='User',
            password='testpass123',
            user_type=UserType.CLIENT.value
        )

    def test_create_client_profile_with_minimal_fields(self):
        """Testa criação de perfil de cliente com campos mínimos."""
        profile = ClientProfile.objects.create(user=self.user)
        
        self.assertEqual(profile.user, self.user)
        self.assertIsNone(profile.address)
        self.assertIsNone(profile.city)
        self.assertIsNone(profile.state)
        self.assertIsNone(profile.zip_code)
        self.assertIsNotNone(profile.created_at)
        self.assertIsNotNone(profile.updated_at)
        self.assertIsNone(profile.deleted_at)

    def test_create_client_profile_with_all_fields(self):
        """Testa criação de perfil de cliente com todos os campos."""
        profile = ClientProfile.objects.create(
            user=self.user,
            address='Rua das Flores, 123',
            city='São Paulo',
            state='SP',
            zip_code='01234-567'
        )
        
        self.assertEqual(profile.address, 'Rua das Flores, 123')
        self.assertEqual(profile.city, 'São Paulo')
        self.assertEqual(profile.state, 'SP')
        self.assertEqual(profile.zip_code, '01234-567')

    def test_one_to_one_relationship(self):
        """Testa que o relacionamento OneToOne funciona corretamente."""
        profile = ClientProfile.objects.create(user=self.user)
        
        # Acessa o perfil através do relacionamento reverso
        self.assertEqual(self.user.client_profile, profile)
        
        # Um User só pode ter um ClientProfile
        with self.assertRaises(IntegrityError):
            ClientProfile.objects.create(user=self.user)

    def test_address_is_optional(self):
        """Testa que address é opcional."""
        profile1 = ClientProfile.objects.create(user=self.user)
        self.assertIsNone(profile1.address)
        
        profile2 = ClientProfile.objects.create(
            user=User.objects.create_user(
                email='client2@example.com',
                first_name='Client',
                last_name='Two',
                password='testpass123',
                user_type=UserType.CLIENT.value
            ),
            address='Rua Teste, 456'
        )
        self.assertEqual(profile2.address, 'Rua Teste, 456')

    def test_city_is_optional(self):
        """Testa que city é opcional."""
        profile1 = ClientProfile.objects.create(user=self.user)
        self.assertIsNone(profile1.city)
        
        profile2 = ClientProfile.objects.create(
            user=User.objects.create_user(
                email='client3@example.com',
                first_name='Client',
                last_name='Three',
                password='testpass123',
                user_type=UserType.CLIENT.value
            ),
            city='Rio de Janeiro'
        )
        self.assertEqual(profile2.city, 'Rio de Janeiro')

    def test_state_is_optional(self):
        """Testa que state é opcional."""
        profile1 = ClientProfile.objects.create(user=self.user)
        self.assertIsNone(profile1.state)
        
        profile2 = ClientProfile.objects.create(
            user=User.objects.create_user(
                email='client4@example.com',
                first_name='Client',
                last_name='Four',
                password='testpass123',
                user_type=UserType.CLIENT.value
            ),
            state='RJ'
        )
        self.assertEqual(profile2.state, 'RJ')

    def test_zip_code_is_optional(self):
        """Testa que zip_code é opcional."""
        profile1 = ClientProfile.objects.create(user=self.user)
        self.assertIsNone(profile1.zip_code)
        
        profile2 = ClientProfile.objects.create(
            user=User.objects.create_user(
                email='client5@example.com',
                first_name='Client',
                last_name='Five',
                password='testpass123',
                user_type=UserType.CLIENT.value
            ),
            zip_code='20000-000'
        )
        self.assertEqual(profile2.zip_code, '20000-000')

    def test_state_max_length(self):
        """Testa que state tem limite de 2 caracteres."""
        profile = ClientProfile.objects.create(user=self.user)
        
        # Estado válido (2 caracteres)
        profile.state = 'SP'
        profile.save()
        self.assertEqual(profile.state, 'SP')
        
        # Estado com mais de 2 caracteres deve ser truncado ou rejeitado
        # (dependendo da validação do Django)
        profile.state = 'SPA'  # 3 caracteres
        with self.assertRaises((ValidationError, ValueError)):
            profile.full_clean()

    def test_address_max_length(self):
        """Testa que address tem limite de 255 caracteres."""
        profile = ClientProfile.objects.create(user=self.user)
        
        # Endereço válido
        profile.address = 'Rua Teste, 123'
        profile.save()
        self.assertEqual(profile.address, 'Rua Teste, 123')
        
        # Endereço muito longo (mais de 255 caracteres)
        long_address = 'A' * 256
        profile.address = long_address
        with self.assertRaises((ValidationError, ValueError)):
            profile.full_clean()

    def test_city_max_length(self):
        """Testa que city tem limite de 100 caracteres."""
        profile = ClientProfile.objects.create(user=self.user)
        
        # Cidade válida
        profile.city = 'São Paulo'
        profile.save()
        self.assertEqual(profile.city, 'São Paulo')
        
        # Cidade muito longa (mais de 100 caracteres)
        long_city = 'A' * 101
        profile.city = long_city
        with self.assertRaises((ValidationError, ValueError)):
            profile.full_clean()

    def test_zip_code_max_length(self):
        """Testa que zip_code tem limite de 10 caracteres."""
        profile = ClientProfile.objects.create(user=self.user)
        
        # CEP válido
        profile.zip_code = '01234-567'
        profile.save()
        self.assertEqual(profile.zip_code, '01234-567')
        
        # CEP muito longo (mais de 10 caracteres)
        long_zip = '0' * 11
        profile.zip_code = long_zip
        with self.assertRaises((ValidationError, ValueError)):
            profile.full_clean()

    def test_str_representation(self):
        """Testa a representação string do modelo."""
        profile = ClientProfile.objects.create(user=self.user)
        expected = f"Perfil de {self.user.email}"
        self.assertEqual(str(profile), expected)

    def test_created_at_auto_now_add(self):
        """Testa que created_at é preenchido automaticamente."""
        before = timezone.now()
        profile = ClientProfile.objects.create(user=self.user)
        after = timezone.now()
        
        self.assertIsNotNone(profile.created_at)
        self.assertGreaterEqual(profile.created_at, before)
        self.assertLessEqual(profile.created_at, after)

    def test_updated_at_auto_now(self):
        """Testa que updated_at é atualizado automaticamente."""
        profile = ClientProfile.objects.create(user=self.user)
        original_updated_at = profile.updated_at
        
        # Aguarda um pouco para garantir diferença de tempo
        time.sleep(0.01)
        
        profile.address = 'Endereço atualizado'
        profile.save()
        
        self.assertGreater(profile.updated_at, original_updated_at)

    def test_soft_delete_functionality(self):
        """Testa funcionalidade de soft delete."""
        profile = ClientProfile.objects.create(user=self.user)
        profile_id = profile.id
        
        # Perfil está ativo
        self.assertIsNone(profile.deleted_at)
        self.assertTrue(profile.is_alive)
        self.assertFalse(profile.is_deleted)
        self.assertEqual(ClientProfile.objects.count(), 1)
        
        # Deleta (soft delete)
        profile.delete()
        profile.refresh_from_db()
        
        # Perfil está deletado
        self.assertIsNotNone(profile.deleted_at)
        self.assertFalse(profile.is_alive)
        self.assertTrue(profile.is_deleted)
        self.assertEqual(ClientProfile.objects.count(), 0)
        self.assertEqual(ClientProfile.all_objects.count(), 1)
        self.assertEqual(ClientProfile.deleted_objects.count(), 1)
        
        # Restaura
        profile.restore()
        profile.refresh_from_db()
        
        # Perfil está ativo novamente
        self.assertIsNone(profile.deleted_at)
        self.assertTrue(profile.is_alive)
        self.assertFalse(profile.is_deleted)
        self.assertEqual(ClientProfile.objects.count(), 1)

    def test_ordering_by_created_at_desc(self):
        """Testa que ordenação padrão é por created_at descendente."""
        # Cria perfis com diferentes timestamps
        user1 = User.objects.create_user(
            email='client1@example.com',
            first_name='Client',
            last_name='One',
            password='pass123',
            user_type=UserType.CLIENT.value
        )
        profile1 = ClientProfile.objects.create(user=user1)
        
        time.sleep(0.01)
        
        user2 = User.objects.create_user(
            email='client2@example.com',
            first_name='Client',
            last_name='Two',
            password='pass123',
            user_type=UserType.CLIENT.value
        )
        profile2 = ClientProfile.objects.create(user=user2)
        
        profiles = list(ClientProfile.objects.all())
        
        # profile2 é mais recente, deve aparecer primeiro
        self.assertEqual(profiles[0], profile2)
        self.assertEqual(profiles[1], profile1)

    def test_indexes_exist(self):
        """Testa que os índices foram criados corretamente."""
        profile = ClientProfile.objects.create(
            user=self.user,
            city='São Paulo',
            state='SP'
        )
        
        # Testa queries que usam os índices (verifica que não há erros)
        ClientProfile.objects.filter(city='São Paulo', state='SP').first()
        ClientProfile.objects.filter(deleted_at__isnull=True).first()
        
        # Verifica que os índices estão definidos no Meta
        index_names = [idx.name for idx in ClientProfile._meta.indexes]
        self.assertIn('client_location_idx', index_names)
        self.assertIn('client_deleted_at_idx', index_names)

    def test_location_index(self):
        """Testa que o índice composto (city, state) funciona corretamente."""
        profile1 = ClientProfile.objects.create(
            user=self.user,
            city='São Paulo',
            state='SP'
        )
        
        user2 = User.objects.create_user(
            email='client6@example.com',
            first_name='Client',
            last_name='Six',
            password='pass123',
            user_type=UserType.CLIENT.value
        )
        profile2 = ClientProfile.objects.create(
            user=user2,
            city='Rio de Janeiro',
            state='RJ'
        )
        
        # Busca por cidade e estado usando o índice
        sp_profiles = ClientProfile.objects.filter(city='São Paulo', state='SP')
        self.assertEqual(sp_profiles.count(), 1)
        self.assertIn(profile1, sp_profiles)
        
        rj_profiles = ClientProfile.objects.filter(city='Rio de Janeiro', state='RJ')
        self.assertEqual(rj_profiles.count(), 1)
        self.assertIn(profile2, rj_profiles)

    def test_user_relationship(self):
        """Testa que o relacionamento com User funciona corretamente."""
        profile = ClientProfile.objects.create(user=self.user)
        
        # Verifica que o perfil está associado ao usuário correto
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.user.email, 'client@example.com')
        
        # Verifica que o usuário pode acessar o perfil
        self.assertEqual(self.user.client_profile, profile)
        
        # Verifica que o usuário é do tipo CLIENT
        self.assertTrue(self.user.is_client)


# =============================================================================
# Testes de Serializers de Autenticação
# =============================================================================

class UserRegisterSerializerTestCase(TestCase):
    """Testes para o UserRegisterSerializer."""

    def test_valid_registration_data(self):
        """Testa registro com dados válidos."""
        data = {
            'email': f'test_{uuid.uuid4().hex[:8]}@example.com',
            'first_name': 'João',
            'last_name': 'Silva',
            'password': 'senha@segura123',
            'password_confirm': 'senha@segura123',
            'user_type': UserType.CLIENT.value,
        }
        serializer = UserRegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_password_mismatch(self):
        """Testa que senhas diferentes geram erro."""
        data = {
            'email': f'test_{uuid.uuid4().hex[:8]}@example.com',
            'first_name': 'João',
            'last_name': 'Silva',
            'password': 'senha@segura123',
            'password_confirm': 'outrasenha123',
            'user_type': UserType.CLIENT.value,
        }
        serializer = UserRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password_confirm', serializer.errors)

    def test_duplicate_email(self):
        """Testa que email duplicado gera erro."""
        email = f'test_{uuid.uuid4().hex[:8]}@example.com'
        User.objects.create_user(
            email=email,
            first_name='Existing',
            last_name='User',
            password='testpass123'
        )
        data = {
            'email': email,
            'first_name': 'João',
            'last_name': 'Silva',
            'password': 'senha@segura123',
            'password_confirm': 'senha@segura123',
        }
        serializer = UserRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_cannot_register_as_admin(self):
        """Testa que não é possível registrar como ADMIN."""
        data = {
            'email': f'test_{uuid.uuid4().hex[:8]}@example.com',
            'first_name': 'João',
            'last_name': 'Silva',
            'password': 'senha@segura123',
            'password_confirm': 'senha@segura123',
            'user_type': UserType.ADMIN.value,
        }
        serializer = UserRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('user_type', serializer.errors)

    def test_creates_client_profile(self):
        """Testa que perfil de cliente é criado automaticamente."""
        data = {
            'email': f'test_{uuid.uuid4().hex[:8]}@example.com',
            'first_name': 'João',
            'last_name': 'Silva',
            'password': 'senha@segura123',
            'password_confirm': 'senha@segura123',
            'user_type': UserType.CLIENT.value,
        }
        serializer = UserRegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertTrue(hasattr(user, 'client_profile'))

    def test_creates_provider_profile(self):
        """Testa que perfil de prestador é criado automaticamente."""
        data = {
            'email': f'test_{uuid.uuid4().hex[:8]}@example.com',
            'first_name': 'João',
            'last_name': 'Silva',
            'password': 'senha@segura123',
            'password_confirm': 'senha@segura123',
            'user_type': UserType.PROVIDER.value,
        }
        serializer = UserRegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertTrue(hasattr(user, 'provider_profile'))


class UserSerializerTestCase(TestCase):
    """Testes para o UserSerializer."""

    def setUp(self):
        """Cria usuário de teste."""
        self.user = User.objects.create_user(
            email=f'test_{uuid.uuid4().hex[:8]}@example.com',
            first_name='João',
            last_name='Silva',
            password='testpass123',
        )
        ClientProfile.objects.create(user=self.user)

    def test_serializes_user_data(self):
        """Testa serialização de dados do usuário."""
        serializer = UserSerializer(self.user)
        data = serializer.data
        
        self.assertEqual(data['email'], self.user.email)
        self.assertEqual(data['first_name'], 'João')
        self.assertEqual(data['last_name'], 'Silva')
        self.assertEqual(data['full_name'], 'João Silva')
        self.assertTrue(data['has_client_profile'])
        self.assertFalse(data['has_provider_profile'])

    def test_read_only_fields(self):
        """Testa que campos read_only não podem ser alterados."""
        serializer = UserSerializer(self.user, data={'email': 'new@example.com'}, partial=True)
        self.assertTrue(serializer.is_valid())
        # email não deve estar nos validated_data pois é read_only
        self.assertNotIn('email', serializer.validated_data)


class UserUpdateSerializerTestCase(TestCase):
    """Testes para o UserUpdateSerializer."""

    def setUp(self):
        """Cria usuário de teste."""
        self.user = User.objects.create_user(
            email=f'test_{uuid.uuid4().hex[:8]}@example.com',
            first_name='João',
            last_name='Silva',
            password='testpass123',
        )

    def test_update_user_data(self):
        """Testa atualização de dados do usuário."""
        serializer = UserUpdateSerializer(
            self.user,
            data={'first_name': 'José', 'phone': '11999998888'},
            partial=True
        )
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.first_name, 'José')
        self.assertEqual(user.phone, '11999998888')

    def test_phone_validation_strips_non_numeric(self):
        """Testa que telefone mantém apenas números."""
        serializer = UserUpdateSerializer(
            self.user,
            data={'phone': '(11) 99999-8888'},
            partial=True
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['phone'], '11999998888')


# =============================================================================
# Testes de Endpoints de Autenticação
# =============================================================================

class RegisterViewTestCase(APITestCase):
    """Testes para o endpoint de registro."""

    def test_register_client_success(self):
        """Testa registro de cliente com sucesso."""
        data = {
            'email': f'newuser_{uuid.uuid4().hex[:8]}@example.com',
            'first_name': 'João',
            'last_name': 'Silva',
            'password': 'senha@segura123',
            'password_confirm': 'senha@segura123',
            'user_type': UserType.CLIENT.value,
        }
        response = self.client.post(reverse('auth-register'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['user_type'], UserType.CLIENT.value)

    def test_register_provider_success(self):
        """Testa registro de prestador com sucesso."""
        data = {
            'email': f'provider_{uuid.uuid4().hex[:8]}@example.com',
            'first_name': 'Maria',
            'last_name': 'Santos',
            'password': 'senha@segura123',
            'password_confirm': 'senha@segura123',
            'user_type': UserType.PROVIDER.value,
        }
        response = self.client.post(reverse('auth-register'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['user_type'], UserType.PROVIDER.value)

    def test_register_invalid_data(self):
        """Testa registro com dados inválidos."""
        data = {
            'email': 'invalid-email',
            'first_name': '',
            'password': '123',  # Muito curta
            'password_confirm': '456',
        }
        response = self.client.post(reverse('auth-register'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email(self):
        """Testa registro com email duplicado."""
        email = f'duplicate_{uuid.uuid4().hex[:8]}@example.com'
        User.objects.create_user(
            email=email,
            first_name='Existing',
            last_name='User',
            password='testpass123'
        )
        data = {
            'email': email,
            'first_name': 'João',
            'last_name': 'Silva',
            'password': 'senha@segura123',
            'password_confirm': 'senha@segura123',
        }
        response = self.client.post(reverse('auth-register'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginViewTestCase(APITestCase):
    """Testes para o endpoint de login."""

    def setUp(self):
        """Cria usuário de teste."""
        self.email = f'login_{uuid.uuid4().hex[:8]}@example.com'
        self.password = 'senha@segura123'
        self.user = User.objects.create_user(
            email=self.email,
            first_name='João',
            last_name='Silva',
            password=self.password,
        )

    def test_login_success(self):
        """Testa login com credenciais válidas."""
        data = {'email': self.email, 'password': self.password}
        response = self.client.post(reverse('auth-login'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)

    def test_login_invalid_credentials(self):
        """Testa login com credenciais inválidas."""
        data = {'email': self.email, 'password': 'wrongpassword'}
        response = self.client.post(reverse('auth-login'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_inactive_user(self):
        """Testa login de usuário inativo."""
        self.user.is_active = False
        self.user.save()
        
        data = {'email': self.email, 'password': self.password}
        response = self.client.post(reverse('auth-login'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutViewTestCase(APITestCase):
    """Testes para o endpoint de logout."""

    def setUp(self):
        """Cria usuário e obtém tokens."""
        self.email = f'logout_{uuid.uuid4().hex[:8]}@example.com'
        self.password = 'senha@segura123'
        self.user = User.objects.create_user(
            email=self.email,
            first_name='João',
            last_name='Silva',
            password=self.password,
        )
        # Faz login para obter tokens
        response = self.client.post(
            reverse('auth-login'),
            {'email': self.email, 'password': self.password},
            format='json'
        )
        self.access_token = response.data['access']
        self.refresh_token = response.data['refresh']

    def test_logout_success(self):
        """Testa logout com token válido."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post(
            reverse('auth-logout'),
            {'refresh': self.refresh_token},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

    def test_logout_without_refresh_token(self):
        """Testa logout sem token de refresh."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post(reverse('auth-logout'), {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_unauthenticated(self):
        """Testa logout sem autenticação."""
        response = self.client.post(
            reverse('auth-logout'),
            {'refresh': self.refresh_token},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RefreshViewTestCase(APITestCase):
    """Testes para o endpoint de refresh de token."""

    def setUp(self):
        """Cria usuário e obtém tokens."""
        self.email = f'refresh_{uuid.uuid4().hex[:8]}@example.com'
        self.password = 'senha@segura123'
        self.user = User.objects.create_user(
            email=self.email,
            first_name='João',
            last_name='Silva',
            password=self.password,
        )
        # Faz login para obter tokens
        response = self.client.post(
            reverse('auth-login'),
            {'email': self.email, 'password': self.password},
            format='json'
        )
        self.refresh_token = response.data['refresh']

    def test_refresh_success(self):
        """Testa refresh de token com sucesso."""
        response = self.client.post(
            reverse('auth-refresh'),
            {'refresh': self.refresh_token},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_refresh_invalid_token(self):
        """Testa refresh com token inválido."""
        response = self.client.post(
            reverse('auth-refresh'),
            {'refresh': 'invalid-token'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MeViewTestCase(APITestCase):
    """Testes para o endpoint /auth/me/."""

    def setUp(self):
        """Cria usuário e autentica."""
        self.email = f'me_{uuid.uuid4().hex[:8]}@example.com'
        self.password = 'senha@segura123'
        self.user = User.objects.create_user(
            email=self.email,
            first_name='João',
            last_name='Silva',
            password=self.password,
        )
        ClientProfile.objects.create(user=self.user)
        # Faz login para obter token
        response = self.client.post(
            reverse('auth-login'),
            {'email': self.email, 'password': self.password},
            format='json'
        )
        self.access_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

    def test_get_me_success(self):
        """Testa GET /auth/me/ com sucesso."""
        response = self.client.get(reverse('auth-me'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.email)
        self.assertEqual(response.data['first_name'], 'João')
        self.assertTrue(response.data['has_client_profile'])

    def test_patch_me_success(self):
        """Testa PATCH /auth/me/ com sucesso."""
        response = self.client.patch(
            reverse('auth-me'),
            {'first_name': 'José', 'phone': '11999998888'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'José')
        
        # Verifica que foi salvo no banco
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'José')
        self.assertEqual(self.user.phone, '11999998888')

    def test_me_unauthenticated(self):
        """Testa acesso sem autenticação."""
        self.client.credentials()  # Remove credenciais
        response = self.client.get(reverse('auth-me'))
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PasswordResetViewTestCase(APITestCase):
    """Testes para os endpoints de reset de senha."""

    def setUp(self):
        """Cria usuário de teste."""
        self.email = f'reset_{uuid.uuid4().hex[:8]}@example.com'
        self.user = User.objects.create_user(
            email=self.email,
            first_name='João',
            last_name='Silva',
            password='senha@segura123',
        )

    def test_password_reset_request_existing_email(self):
        """Testa solicitação de reset para email existente."""
        response = self.client.post(
            reverse('auth-password-reset'),
            {'email': self.email},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

    def test_password_reset_request_nonexistent_email(self):
        """Testa solicitação de reset para email inexistente (deve retornar sucesso por segurança)."""
        response = self.client.post(
            reverse('auth-password-reset'),
            {'email': 'nonexistent@example.com'},
            format='json'
        )
        
        # Sempre retorna sucesso por segurança
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_reset_confirm_success(self):
        """Testa confirmação de reset de senha com sucesso."""
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        from django.contrib.auth.tokens import default_token_generator
        
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        
        response = self.client.post(
            reverse('auth-password-reset-confirm'),
            {
                'uid': uid,
                'token': token,
                'new_password': 'novasenha@segura123',
                'new_password_confirm': 'novasenha@segura123',
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verifica que a senha foi alterada
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('novasenha@segura123'))

    def test_password_reset_confirm_invalid_token(self):
        """Testa confirmação com token inválido."""
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        response = self.client.post(
            reverse('auth-password-reset-confirm'),
            {
                'uid': uid,
                'token': 'invalid-token',
                'new_password': 'novasenha@segura123',
                'new_password_confirm': 'novasenha@segura123',
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_confirm_password_mismatch(self):
        """Testa confirmação com senhas diferentes."""
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        from django.contrib.auth.tokens import default_token_generator
        
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        
        response = self.client.post(
            reverse('auth-password-reset-confirm'),
            {
                'uid': uid,
                'token': token,
                'new_password': 'novasenha@segura123',
                'new_password_confirm': 'outrasenha@123',
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# =============================================================================
# Testes de Permissões
# =============================================================================


class MockRequest:
    """Mock de request para testes de permissões."""
    
    def __init__(self, user=None):
        self.user = user


class MockView:
    """Mock de view para testes de permissões."""
    pass


class IsClientPermissionTestCase(TestCase):
    """Testes para a permissão IsClient."""

    def setUp(self):
        """Cria dados de teste."""
        self.unique_id = str(uuid.uuid4())[:8]
        self.client_user = User.objects.create_user(
            email=f'client-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Client',
            last_name='User',
            user_type=UserType.CLIENT.value,
        )
        self.provider_user = User.objects.create_user(
            email=f'provider-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Provider',
            last_name='User',
            user_type=UserType.PROVIDER.value,
        )
        self.admin_user = User.objects.create_user(
            email=f'admin-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Admin',
            last_name='User',
            user_type=UserType.ADMIN.value,
        )

    def test_client_user_has_permission(self):
        """Testa que cliente tem permissão."""
        from api.accounts.permissions import IsClient
        
        permission = IsClient()
        request = MockRequest(user=self.client_user)
        
        self.assertTrue(permission.has_permission(request, MockView()))

    def test_provider_user_denied(self):
        """Testa que prestador é negado."""
        from api.accounts.permissions import IsClient
        
        permission = IsClient()
        request = MockRequest(user=self.provider_user)
        
        self.assertFalse(permission.has_permission(request, MockView()))

    def test_admin_user_denied(self):
        """Testa que admin é negado."""
        from api.accounts.permissions import IsClient
        
        permission = IsClient()
        request = MockRequest(user=self.admin_user)
        
        self.assertFalse(permission.has_permission(request, MockView()))

    def test_unauthenticated_user_denied(self):
        """Testa que usuário não autenticado é negado."""
        from api.accounts.permissions import IsClient
        from django.contrib.auth.models import AnonymousUser
        
        permission = IsClient()
        request = MockRequest(user=AnonymousUser())
        
        self.assertFalse(permission.has_permission(request, MockView()))

    def test_no_user_denied(self):
        """Testa que request sem usuário é negado."""
        from api.accounts.permissions import IsClient
        
        permission = IsClient()
        request = MockRequest(user=None)
        
        self.assertFalse(permission.has_permission(request, MockView()))


class IsProviderPermissionTestCase(TestCase):
    """Testes para a permissão IsProvider."""

    def setUp(self):
        """Cria dados de teste."""
        self.unique_id = str(uuid.uuid4())[:8]
        self.client_user = User.objects.create_user(
            email=f'client-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Client',
            last_name='User',
            user_type=UserType.CLIENT.value,
        )
        self.provider_user = User.objects.create_user(
            email=f'provider-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Provider',
            last_name='User',
            user_type=UserType.PROVIDER.value,
        )
        self.admin_user = User.objects.create_user(
            email=f'admin-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Admin',
            last_name='User',
            user_type=UserType.ADMIN.value,
        )

    def test_provider_user_has_permission(self):
        """Testa que prestador tem permissão."""
        from api.accounts.permissions import IsProvider
        
        permission = IsProvider()
        request = MockRequest(user=self.provider_user)
        
        self.assertTrue(permission.has_permission(request, MockView()))

    def test_client_user_denied(self):
        """Testa que cliente é negado."""
        from api.accounts.permissions import IsProvider
        
        permission = IsProvider()
        request = MockRequest(user=self.client_user)
        
        self.assertFalse(permission.has_permission(request, MockView()))

    def test_admin_user_denied(self):
        """Testa que admin é negado."""
        from api.accounts.permissions import IsProvider
        
        permission = IsProvider()
        request = MockRequest(user=self.admin_user)
        
        self.assertFalse(permission.has_permission(request, MockView()))

    def test_unauthenticated_user_denied(self):
        """Testa que usuário não autenticado é negado."""
        from api.accounts.permissions import IsProvider
        from django.contrib.auth.models import AnonymousUser
        
        permission = IsProvider()
        request = MockRequest(user=AnonymousUser())
        
        self.assertFalse(permission.has_permission(request, MockView()))


class IsAdminPermissionTestCase(TestCase):
    """Testes para a permissão IsAdmin."""

    def setUp(self):
        """Cria dados de teste."""
        self.unique_id = str(uuid.uuid4())[:8]
        self.client_user = User.objects.create_user(
            email=f'client-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Client',
            last_name='User',
            user_type=UserType.CLIENT.value,
        )
        self.admin_user = User.objects.create_user(
            email=f'admin-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Admin',
            last_name='User',
            user_type=UserType.ADMIN.value,
        )
        self.staff_user = User.objects.create_user(
            email=f'staff-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Staff',
            last_name='User',
            user_type=UserType.CLIENT.value,
            is_staff=True,
        )
        self.superuser = User.objects.create_superuser(
            email=f'super-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Super',
            last_name='User',
        )

    def test_admin_user_has_permission(self):
        """Testa que usuário com user_type ADMIN tem permissão."""
        from api.accounts.permissions import IsAdmin
        
        permission = IsAdmin()
        request = MockRequest(user=self.admin_user)
        
        self.assertTrue(permission.has_permission(request, MockView()))

    def test_staff_user_has_permission(self):
        """Testa que usuário com is_staff tem permissão."""
        from api.accounts.permissions import IsAdmin
        
        permission = IsAdmin()
        request = MockRequest(user=self.staff_user)
        
        self.assertTrue(permission.has_permission(request, MockView()))

    def test_superuser_has_permission(self):
        """Testa que superuser tem permissão."""
        from api.accounts.permissions import IsAdmin
        
        permission = IsAdmin()
        request = MockRequest(user=self.superuser)
        
        self.assertTrue(permission.has_permission(request, MockView()))

    def test_client_user_denied(self):
        """Testa que cliente comum é negado."""
        from api.accounts.permissions import IsAdmin
        
        permission = IsAdmin()
        request = MockRequest(user=self.client_user)
        
        self.assertFalse(permission.has_permission(request, MockView()))

    def test_unauthenticated_user_denied(self):
        """Testa que usuário não autenticado é negado."""
        from api.accounts.permissions import IsAdmin
        from django.contrib.auth.models import AnonymousUser
        
        permission = IsAdmin()
        request = MockRequest(user=AnonymousUser())
        
        self.assertFalse(permission.has_permission(request, MockView()))


class IsClientOrProviderPermissionTestCase(TestCase):
    """Testes para a permissão IsClientOrProvider."""

    def setUp(self):
        """Cria dados de teste."""
        self.unique_id = str(uuid.uuid4())[:8]
        self.client_user = User.objects.create_user(
            email=f'client-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Client',
            last_name='User',
            user_type=UserType.CLIENT.value,
        )
        self.provider_user = User.objects.create_user(
            email=f'provider-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Provider',
            last_name='User',
            user_type=UserType.PROVIDER.value,
        )
        self.admin_user = User.objects.create_user(
            email=f'admin-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Admin',
            last_name='User',
            user_type=UserType.ADMIN.value,
        )

    def test_client_user_has_permission(self):
        """Testa que cliente tem permissão."""
        from api.accounts.permissions import IsClientOrProvider
        
        permission = IsClientOrProvider()
        request = MockRequest(user=self.client_user)
        
        self.assertTrue(permission.has_permission(request, MockView()))

    def test_provider_user_has_permission(self):
        """Testa que prestador tem permissão."""
        from api.accounts.permissions import IsClientOrProvider
        
        permission = IsClientOrProvider()
        request = MockRequest(user=self.provider_user)
        
        self.assertTrue(permission.has_permission(request, MockView()))

    def test_admin_user_denied(self):
        """Testa que admin é negado."""
        from api.accounts.permissions import IsClientOrProvider
        
        permission = IsClientOrProvider()
        request = MockRequest(user=self.admin_user)
        
        self.assertFalse(permission.has_permission(request, MockView()))


class IsOwnerOrAdminPermissionTestCase(TestCase):
    """Testes para a permissão IsOwnerOrAdmin."""

    def setUp(self):
        """Cria dados de teste."""
        self.unique_id = str(uuid.uuid4())[:8]
        self.owner_user = User.objects.create_user(
            email=f'owner-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Owner',
            last_name='User',
            user_type=UserType.CLIENT.value,
        )
        self.other_user = User.objects.create_user(
            email=f'other-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Other',
            last_name='User',
            user_type=UserType.CLIENT.value,
        )
        self.admin_user = User.objects.create_user(
            email=f'admin-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Admin',
            last_name='User',
            user_type=UserType.ADMIN.value,
        )

    def test_owner_has_permission(self):
        """Testa que dono tem permissão."""
        from api.accounts.permissions import IsOwnerOrAdmin
        
        permission = IsOwnerOrAdmin()
        request = MockRequest(user=self.owner_user)
        
        # Mock de objeto com atributo 'user'
        class MockObj:
            def __init__(self, user):
                self.user = user
        
        obj = MockObj(user=self.owner_user)
        
        self.assertTrue(permission.has_object_permission(request, MockView(), obj))

    def test_admin_has_permission_on_any_object(self):
        """Testa que admin tem permissão em qualquer objeto."""
        from api.accounts.permissions import IsOwnerOrAdmin
        
        permission = IsOwnerOrAdmin()
        request = MockRequest(user=self.admin_user)
        
        class MockObj:
            def __init__(self, user):
                self.user = user
        
        obj = MockObj(user=self.owner_user)  # Objeto de outro usuário
        
        self.assertTrue(permission.has_object_permission(request, MockView(), obj))

    def test_non_owner_denied(self):
        """Testa que não-dono é negado."""
        from api.accounts.permissions import IsOwnerOrAdmin
        
        permission = IsOwnerOrAdmin()
        request = MockRequest(user=self.other_user)
        
        class MockObj:
            def __init__(self, user):
                self.user = user
        
        obj = MockObj(user=self.owner_user)
        
        self.assertFalse(permission.has_object_permission(request, MockView(), obj))

    def test_owner_via_client_attribute(self):
        """Testa permissão via atributo 'client'."""
        from api.accounts.permissions import IsOwnerOrAdmin
        
        permission = IsOwnerOrAdmin()
        request = MockRequest(user=self.owner_user)
        
        class MockObj:
            def __init__(self, client):
                self.client = client
        
        obj = MockObj(client=self.owner_user)
        
        self.assertTrue(permission.has_object_permission(request, MockView(), obj))

    def test_owner_via_provider_attribute(self):
        """Testa permissão via atributo 'provider'."""
        from api.accounts.permissions import IsOwnerOrAdmin
        
        permission = IsOwnerOrAdmin()
        request = MockRequest(user=self.owner_user)
        
        class MockObj:
            def __init__(self, provider):
                self.provider = provider
        
        obj = MockObj(provider=self.owner_user)
        
        self.assertTrue(permission.has_object_permission(request, MockView(), obj))

    def test_owner_via_get_owner_method(self):
        """Testa permissão via método 'get_owner()'."""
        from api.accounts.permissions import IsOwnerOrAdmin
        
        permission = IsOwnerOrAdmin()
        request = MockRequest(user=self.owner_user)
        
        class MockObj:
            def __init__(self, owner):
                self._owner = owner
            
            def get_owner(self):
                return self._owner
        
        obj = MockObj(owner=self.owner_user)
        
        self.assertTrue(permission.has_object_permission(request, MockView(), obj))
