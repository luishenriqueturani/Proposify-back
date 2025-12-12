"""
Custom managers for Soft Delete functionality.
"""
from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet customizado para Soft Delete."""

    def delete(self):
        """Marca todos os registros do queryset como deletados."""
        return self.update(deleted_at=timezone.now())

    def hard_delete(self):
        """Remove fisicamente os registros do banco."""
        return super().delete()

    def restore(self):
        """Restaura todos os registros deletados do queryset."""
        return self.update(deleted_at=None)

    def alive(self):
        """Retorna apenas registros não deletados."""
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        """Retorna apenas registros deletados."""
        return self.filter(deleted_at__isnull=False)


class SoftDeleteManager(models.Manager):
    """
    Manager customizado que filtra automaticamente registros deletados.
    
    Uso:
        - objects: retorna apenas registros não deletados (padrão)
        - all_objects: retorna todos os registros (incluindo deletados)
        - deleted_objects: retorna apenas registros deletados
    """

    def get_queryset(self):
        """Retorna queryset filtrando registros deletados."""
        return SoftDeleteQuerySet(self.model, using=self._db).filter(
            deleted_at__isnull=True
        )

    def all_objects(self):
        """Retorna todos os registros, incluindo deletados."""
        return SoftDeleteQuerySet(self.model, using=self._db)

    def deleted_objects(self):
        """Retorna apenas registros deletados."""
        return SoftDeleteQuerySet(self.model, using=self._db).filter(
            deleted_at__isnull=False
        )

    def alive(self):
        """Retorna apenas registros não deletados (alias para get_queryset)."""
        return self.get_queryset()

    def dead(self):
        """Retorna apenas registros deletados."""
        return self.deleted_objects()

