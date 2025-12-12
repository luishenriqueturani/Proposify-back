"""
Base models and mixins for Soft Delete functionality.
"""
from django.db import models
from django.utils import timezone
from .managers import SoftDeleteManager, SoftDeleteQuerySet


class SoftDeleteMixin(models.Model):
    """
    Mixin que adiciona funcionalidade de Soft Delete a um modelo.
    
    Adiciona:
        - Campo deleted_at (DateTimeField, nullable)
        - Manager customizado que filtra registros deletados
        - Métodos: delete(), hard_delete(), restore()
    
    Uso:
        class MyModel(SoftDeleteMixin, models.Model):
            name = models.CharField(max_length=100)
            
        # Queries normais excluem deletados automaticamente
        MyModel.objects.all()  # apenas não deletados
        
        # Para incluir deletados
        MyModel.all_objects.all()  # todos
        
        # Para buscar apenas deletados
        MyModel.deleted_objects.all()  # apenas deletados
    """

    deleted_at = models.DateTimeField(  # type: ignore
        null=True,
        blank=True,
        db_index=True,
        verbose_name='Data de Exclusão',
        help_text='Data e hora em que o registro foi deletado. NULL significa que está ativo.'
    )

    objects = SoftDeleteManager()

    class AllObjectsManager(models.Manager):
        """Manager para acessar todos os registros (incluindo deletados)."""
        def get_queryset(self):
            return SoftDeleteQuerySet(self.model, using=self._db)
    
    all_objects = AllObjectsManager()
    
    class DeletedObjectsManager(models.Manager):
        """Manager para acessar apenas registros deletados."""
        def get_queryset(self):
            return SoftDeleteQuerySet(self.model, using=self._db).filter(
                deleted_at__isnull=False
            )
    
    deleted_objects = DeletedObjectsManager()

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['deleted_at'], name='%(class)s_deleted_at_idx'),
        ]

    def delete(self, using=None, keep_parents=False):
        """
        Soft delete: marca o registro como deletado sem removê-lo do banco.
        
        Args:
            using: Database alias (não usado em soft delete)
            keep_parents: Mantém registros pais (não usado em soft delete)
        """
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def hard_delete(self, using=None, keep_parents=False):
        """
        Hard delete: remove fisicamente o registro do banco.
        
        Use com cuidado! Esta operação não pode ser desfeita.
        
        Args:
            using: Database alias
            keep_parents: Mantém registros pais
        """
        return super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        """
        Restaura um registro deletado, definindo deleted_at como NULL.
        
        Returns:
            bool: True se o registro foi restaurado, False caso contrário
        """
        if self.deleted_at is None:
            return False
        
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])
        return True

    @property
    def is_deleted(self):
        """Retorna True se o registro está deletado."""
        return self.deleted_at is not None

    @property
    def is_alive(self):
        """Retorna True se o registro está ativo (não deletado)."""
        return self.deleted_at is None


class SoftDeleteModel(SoftDeleteMixin, models.Model):
    """
    Modelo base com Soft Delete já implementado.
    
    Use esta classe como base para modelos que precisam de soft delete.
    Todos os modelos que herdam desta classe terão:
        - Campo deleted_at
        - Manager customizado
        - Métodos delete(), hard_delete(), restore()
    
    Exemplo:
        class MyModel(SoftDeleteModel):
            name = models.CharField(max_length=100)
            created_at = models.DateTimeField(auto_now_add=True)
    """

    class Meta:
        abstract = True
