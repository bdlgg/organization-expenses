"""Django ORM-модели справочников организации."""

from django.db import models


class Category(models.Model):
    """Категория, к которой относится расход."""

    name = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Название категории",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Категория расходов"
        verbose_name_plural = "Категории расходов"

    def __str__(self) -> str:
        return self.name


class Department(models.Model):
    """Подразделение организации, учитывающее расходы."""

    name = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Название подразделения",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Подразделение"
        verbose_name_plural = "Подразделения"

    def __str__(self) -> str:
        return self.name


class Document(models.Model):
    """Первичный документ, подтверждающий расход."""

    number = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Номер документа",
    )

    class Meta:
        ordering = ["number"]
        verbose_name = "Документ"
        verbose_name_plural = "Документы"

    def __str__(self) -> str:
        return self.number
