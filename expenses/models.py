
"""Django ORM-модель расходов организации."""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse

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
    comment = models.TextField(
        "Комментарий",
        blank=True,
        default="Без комментария",
    )
    slug = models.SlugField(
        max_length=160,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Адрес расхода",
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

    def save(self, *args, **kwargs):
        """Сохранить расход и при необходимости сформировать slug."""
        if not self.pk:
            super().save(*args, **kwargs)

        if not self.slug:
            self.slug = f"expense-{self.pk}"
            kwargs.pop("force_insert", None)
            super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Вернуть адрес страницы расхода."""
        return reverse(
            "expenses:expense_detail",
            kwargs={"slug": self.slug},
        )

    def __str__(self):
        return (
            f"Расход №{self.pk}: {self.amount:.2f} ₽ — "
            f"{self.category}, {self.department}"
        )
