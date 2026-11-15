"""Django ORM-модель расходов организации."""

import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from unidecode import unidecode

from catalogs.models import Category, Department, Document


class ExpenseQuerySet(models.QuerySet):
    """Переиспользуемые выборки расходов по статусу и дате."""

    def pending(self):
        """Расходы, ожидающие обработки."""
        return self.filter(status=self.model.Status.PENDING)

    def approved(self):
        """Расходы, одобренные ответственным сотрудником."""
        return self.filter(status=self.model.Status.APPROVED)

    def paid(self):
        """Оплаченные расходы."""
        return self.filter(status=self.model.Status.PAID)

    def cancelled(self):
        """Отменённые расходы."""
        return self.filter(status=self.model.Status.CANCELLED)

    def not_cancelled(self):
        """Расходы, не помеченные как отменённые."""
        return self.exclude(status=self.model.Status.CANCELLED)

    def for_date(self, selected_date):
        """Расходы за конкретную дату."""
        return self.filter(expense_date=selected_date)

    def for_period(self, date_from=None, date_to=None):
        """Расходы в заданном диапазоне дат."""
        queryset = self
        if date_from is not None:
            queryset = queryset.filter(expense_date__gte=date_from)
        if date_to is not None:
            queryset = queryset.filter(expense_date__lte=date_to)
        return queryset

    def above_amount(self, minimum):
        """Расходы не меньше указанной суммы."""
        return self.filter(amount__gte=minimum)


class ExpenseManager(models.Manager.from_queryset(ExpenseQuerySet)):
    """Менеджер с предметными методами выборки расходов."""


class Expense(models.Model):
    """Расход организации со ссылками на справочники."""

    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает обработки"
        APPROVED = "approved", "Одобрен"
        PAID = "paid", "Оплачен"
        CANCELLED = "cancelled", "Отменён"

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Сумма расхода",
        help_text="Сумма в рублях. Отрицательные значения не допускаются.",
    )
    expense_date = models.DateField(
        default=timezone.localdate,
        null=True,
        blank=True,
        verbose_name="Дата расхода",
        help_text=(
            "Дата операции. Для ранее импортированных записей без даты "
            "значение может оставаться пустым."
        ),
    )
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Статус расхода",
        help_text="Состояние обработки или оплаты расхода.",
    )
    slug = models.SlugField(
        max_length=180,
        unique=True,
        blank=True,
        editable=False,
        verbose_name="Адрес карточки",
    )
    is_large = models.GeneratedField(
        expression=models.Case(
            models.When(
                amount__gte=Decimal("10000.00"),
                then=models.Value(True),
            ),
            default=models.Value(False),
            output_field=models.BooleanField(),
        ),
        output_field=models.BooleanField(),
        db_persist=True,
        verbose_name="Крупный расход",
        help_text="Автоматически определяется по порогу 10 000 ₽.",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="expenses",
        verbose_name="Категория",
        help_text="Справочник категории, к которой относится расход.",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="expenses",
        verbose_name="Подразделение",
        help_text="Подразделение, для которого учтён расход.",
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.PROTECT,
        related_name="expenses",
        verbose_name="Подтверждающий документ",
        help_text="Документ, подтверждающий операцию.",
    )

    objects = ExpenseManager()

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
            models.Index(
                fields=["status", "expense_date"],
                name="expense_status_date_idx",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"Расход №{self.pk}: {self.amount:.2f} ₽ — "
            f"{self.category}, {self.department}"
        )

    def _build_slug(self) -> str:
        """Сформировать стабильный уникальный URL по расходу и справочникам."""
        category_name = self.category.name if self.category_id else ""
        department_name = self.department.name if self.department_id else ""
        base = slugify(
            unidecode(f"raskhod-{category_name}-{department_name}")
        ) or "raskhod"
        suffix = f"-{self.pk}"
        return f"{base[:180 - len(suffix)].rstrip('-')}{suffix}"

    def save(self, *args, **kwargs):
        """Автоматически сформировать slug для новой записи расхода."""
        if self._state.adding and not self.slug:
            # Сначала сохраняем временный уникальный slug, чтобы получить PK.
            self.slug = f"temporary-{uuid.uuid4().hex}"
            super().save(*args, **kwargs)
            self.slug = self._build_slug()
            super().save(update_fields=["slug"])
            return

        if not self.slug:
            self.slug = self._build_slug()
            update_fields = kwargs.get("update_fields")
            if update_fields is not None:
                kwargs["update_fields"] = set(update_fields) | {"slug"}

        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        """Вернуть канонический адрес подробной страницы расхода."""
        return reverse(
            "expenses:expense_detail",
            kwargs={"slug": self.slug},
        )
