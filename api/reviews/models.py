"""
Models para o app reviews (avaliações).
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from api.utils.models import SoftDeleteMixin


class Review(SoftDeleteMixin, models.Model):
    """
    Avaliação feita por um usuário sobre outro usuário após conclusão de um pedido.
    Permite que clientes avaliem prestadores e vice-versa.
    """
    order = models.ForeignKey(  # type: ignore
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Pedido',
        help_text='Pedido ao qual esta avaliação se refere'
    )

    reviewer = models.ForeignKey(  # type: ignore
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='reviews_given',
        verbose_name='Avaliador',
        help_text='Usuário que fez a avaliação'
    )

    reviewed_user = models.ForeignKey(  # type: ignore
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='reviews_received',
        verbose_name='Avaliado',
        help_text='Usuário que foi avaliado'
    )

    rating = models.PositiveIntegerField(  # type: ignore
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Avaliação',
        help_text='Nota de 1 a 5 estrelas'
    )

    comment = models.TextField(  # type: ignore
        blank=True,
        null=True,
        verbose_name='Comentário',
        help_text='Comentário opcional sobre a avaliação'
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
        verbose_name = 'Avaliação'
        verbose_name_plural = 'Avaliações'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order'], name='review_order_idx'),
            models.Index(fields=['reviewer'], name='review_reviewer_idx'),
            models.Index(fields=['reviewed_user'], name='review_reviewed_user_idx'),
            models.Index(fields=['rating'], name='review_rating_idx'),
            models.Index(fields=['deleted_at'], name='review_deleted_at_idx'),
        ]
        # Índice único: (order, reviewer) - garante que cada usuário só pode avaliar uma vez por pedido
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'reviewer'],
                name='unique_review_order_reviewer'
            )
        ]

    def __str__(self):
        return f"Avaliação #{self.id} - {self.reviewer.email} avaliou {self.reviewed_user.email} ({self.rating}/5)"

    def clean(self):
        """Valida que o avaliador e o avaliado são diferentes."""
        from django.core.exceptions import ValidationError
        if self.reviewer == self.reviewed_user:
            raise ValidationError('Um usuário não pode se avaliar.')

    def save(self, *args, **kwargs):
        """Valida antes de salvar."""
        self.full_clean()
        super().save(*args, **kwargs)
