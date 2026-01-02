"""
Testes unitários para os modelos do app accounts.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from decimal import Decimal
import time

from api.accounts.models import User, ProviderProfile, ClientProfile
from api.accounts.enums import UserType


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
        time.sleep(0.01)
        
        user.first_name = 'Updated'
        user.save()
        
        self.assertGreater(user.updated_at, original_updated_at)

    def test_soft_delete_functionality(self):
        """Testa funcionalidade de soft delete."""
        user = User.objects.create_user(**self.user_data)
        
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
