"""Django ORM-модель расходов организации."""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from catalogs.models import Category, Department, Document


class Expense(models.Model):
    """Расход организации со ссылками на справочники."""

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Сумма расхода",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="expenses",
        verbose_name="Категория",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="expenses",
        verbose_name="Подразделение",
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.PROTECT,
        related_name="expenses",
        verbose_name="Подтверждающий документ",
    )

    class Meta:
        ordering = ["-amount", "pk"]
        verbose_name = "Расход"
        verbose_name_plural = "Расходы"
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gte=Decimal("0.00")),
                name="expense_amount_non_negative",
            ),
        ]
        indexes = [
            models.Index(fields=["amount"], name="expense_amount_idx"),
        ]

    def __str__(self) -> str:
        return (
            f"Расход №{self.pk}: {self.amount:.2f} ₽ — "
            f"{self.category}, {self.department}"
        )
