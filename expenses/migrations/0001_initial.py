# Generated for PR9: the Expense model and its catalog relationships.

import decimal

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("catalogs", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Expense",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[
                            django.core.validators.MinValueValidator(
                                decimal.Decimal("0.00")
                            ),
                        ],
                        verbose_name="Сумма расхода",
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="expenses",
                        to="catalogs.category",
                        verbose_name="Категория",
                    ),
                ),
                (
                    "department",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="expenses",
                        to="catalogs.department",
                        verbose_name="Подразделение",
                    ),
                ),
                (
                    "document",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="expenses",
                        to="catalogs.document",
                        verbose_name="Подтверждающий документ",
                    ),
                ),
            ],
            options={
                "verbose_name": "Расход",
                "verbose_name_plural": "Расходы",
                "ordering": ["-amount", "pk"],
            },
        ),
        migrations.AddConstraint(
            model_name="expense",
            constraint=models.CheckConstraint(
                condition=models.Q(amount__gte=decimal.Decimal("0.00")),
                name="expense_amount_non_negative",
            ),
        ),
        migrations.AddIndex(
            model_name="expense",
            index=models.Index(
                fields=["amount"],
                name="expense_amount_idx",
            ),
        ),
    ]
