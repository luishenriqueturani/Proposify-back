"""
Models para o app services (categorias e serviços).
"""
from django.db import models
from django.utils.text import slugify
from api.utils.models import SoftDeleteMixin


class ServiceCategory(SoftDeleteMixin, models.Model):
    """
    Categoria de serviço.
    Suporta hierarquia de categorias e subcategorias através do campo parent.
    """
    name = models.CharField(  # type: ignore
        max_length=100,
        unique=True,
        verbose_name='Nome',
        help_text='Nome da categoria de serviço'
    )

    slug = models.SlugField(  # type: ignore
        max_length=100,
        unique=True,
        blank=True,
        verbose_name='Slug',
        help_text='Slug único para a categoria (gerado automaticamente se não fornecido)'
    )

    description = models.TextField(  # type: ignore
        blank=True,
        null=True,
        verbose_name='Descrição',
        help_text='Descrição detalhada da categoria'
    )

    parent = models.ForeignKey(  # type: ignore
        'self',
        on_delete=models.CASCADE,
        related_name='children',
        blank=True,
        null=True,
        verbose_name='Categoria Pai',
        help_text='Categoria pai para criar subcategorias (deixe em branco para categoria principal)'
    )

    is_active = models.BooleanField(  # type: ignore
        default=True,
        verbose_name='Ativo',
        help_text='Indica se a categoria está ativa e disponível'
    )

    # Campos de timestamp
    created_at = models.DateTimeField(  # type: ignore
        auto_now_add=True,
        verbose_name='Data de Criação'
    )

    updated_at = models.DateTimeField(  # type: ignore
        auto_now=True,
        verbose_name='Data de Atualização'
    )

    class Meta:
        verbose_name = 'Categoria de Serviço'
        verbose_name_plural = 'Categorias de Serviços'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug'], name='category_slug_idx'),
            models.Index(fields=['parent'], name='category_parent_idx'),
            models.Index(fields=['is_active'], name='category_is_active_idx'),
            models.Index(fields=['deleted_at'], name='category_deleted_at_idx'),
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        """Gera slug automaticamente se não fornecido."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def is_subcategory(self):
        """Retorna True se esta categoria é uma subcategoria."""
        return self.parent is not None

    def get_full_path(self):
        """Retorna o caminho completo da categoria (ex: 'Pai > Filho > Neto')."""
        path = [self.name]
        current = self.parent
        while current:
            path.insert(0, current.name)
            current = current.parent
        return ' > '.join(path)


class Service(SoftDeleteMixin, models.Model):
    """
    Serviço oferecido na plataforma.
    Cada serviço pertence a uma categoria.
    """
    category = models.ForeignKey(  # type: ignore
        ServiceCategory,
        on_delete=models.CASCADE,
        related_name='services',
        verbose_name='Categoria',
        help_text='Categoria à qual este serviço pertence'
    )

    name = models.CharField(  # type: ignore
        max_length=200,
        verbose_name='Nome',
        help_text='Nome do serviço'
    )

    description = models.TextField(  # type: ignore
        blank=True,
        null=True,
        verbose_name='Descrição',
        help_text='Descrição detalhada do serviço'
    )

    is_active = models.BooleanField(  # type: ignore
        default=True,
        verbose_name='Ativo',
        help_text='Indica se o serviço está ativo e disponível'
    )

    # Campos de timestamp
    created_at = models.DateTimeField(  # type: ignore
        auto_now_add=True,
        verbose_name='Data de Criação'
    )

    updated_at = models.DateTimeField(  # type: ignore
        auto_now=True,
        verbose_name='Data de Atualização'
    )

    class Meta:
        verbose_name = 'Serviço'
        verbose_name_plural = 'Serviços'
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['category'], name='service_category_idx'),
            models.Index(fields=['is_active'], name='service_is_active_idx'),
            models.Index(fields=['deleted_at'], name='service_deleted_at_idx'),
        ]

    def __str__(self):
        return f"{self.name} ({self.category.name})"
