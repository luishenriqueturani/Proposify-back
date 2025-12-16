# Generated manually to create initial subscription plans

from django.db import migrations


def create_initial_plans(apps, schema_editor):
    """Cria os planos iniciais: FREE, BASIC, PREMIUM, ENTERPRISE."""
    SubscriptionPlan = apps.get_model('subscriptions', 'SubscriptionPlan')

    plans = [
        {
            'name': 'FREE',
            'slug': 'free',
            'description': 'Plano gratuito com recursos básicos',
            'price_monthly': 0.00,
            'price_yearly': 0.00,
            'features': {
                'max_orders_per_month': 5,
                'max_proposals_per_order': 3,
                'chat_support': True,
                'basic_analytics': True,
            },
            'max_orders_per_month': 5,
            'max_proposals_per_order': 3,
            'is_active': True,
            'is_default': True,
        },
        {
            'name': 'BASIC',
            'slug': 'basic',
            'description': 'Plano básico com recursos intermediários',
            'price_monthly': 29.90,
            'price_yearly': 299.00,
            'features': {
                'max_orders_per_month': 20,
                'max_proposals_per_order': 10,
                'chat_support': True,
                'priority_support': True,
                'advanced_analytics': True,
            },
            'max_orders_per_month': 20,
            'max_proposals_per_order': 10,
            'is_active': True,
            'is_default': False,
        },
        {
            'name': 'PREMIUM',
            'slug': 'premium',
            'description': 'Plano premium com recursos avançados',
            'price_monthly': 79.90,
            'price_yearly': 799.00,
            'features': {
                'max_orders_per_month': 0,  # Ilimitado
                'max_proposals_per_order': 0,  # Ilimitado
                'chat_support': True,
                'priority_support': True,
                'advanced_analytics': True,
                'custom_branding': True,
                'api_access': True,
            },
            'max_orders_per_month': 0,  # Ilimitado
            'max_proposals_per_order': 0,  # Ilimitado
            'is_active': True,
            'is_default': False,
        },
        {
            'name': 'ENTERPRISE',
            'slug': 'enterprise',
            'description': 'Plano empresarial com recursos completos e suporte dedicado',
            'price_monthly': 199.90,
            'price_yearly': 1999.00,
            'features': {
                'max_orders_per_month': 0,  # Ilimitado
                'max_proposals_per_order': 0,  # Ilimitado
                'chat_support': True,
                'priority_support': True,
                'dedicated_support': True,
                'advanced_analytics': True,
                'custom_branding': True,
                'api_access': True,
                'white_label': True,
                'custom_integrations': True,
            },
            'max_orders_per_month': 0,  # Ilimitado
            'max_proposals_per_order': 0,  # Ilimitado
            'is_active': True,
            'is_default': False,
        },
    ]

    for plan_data in plans:
        SubscriptionPlan.objects.get_or_create(
            slug=plan_data['slug'],
            defaults=plan_data
        )


def reverse_create_initial_plans(apps, schema_editor):
    """Remove os planos iniciais."""
    SubscriptionPlan = apps.get_model('subscriptions', 'SubscriptionPlan')
    SubscriptionPlan.objects.filter(slug__in=['free', 'basic', 'premium', 'enterprise']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_plans, reverse_create_initial_plans),
    ]

