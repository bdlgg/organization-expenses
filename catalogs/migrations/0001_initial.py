# Generated for PR9: Django ORM models for organization catalogs.

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Category",
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
                    "name",
                    models.CharField(
                        max_length=150,
                        unique=True,
                        verbose_name="Название категории",
                    ),
                ),
            ],
            options={
                "verbose_name": "Категория расходов",
                "verbose_name_plural": "Категории расходов",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Department",
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
                    "name",
                    models.CharField(
                        max_length=150,
                        unique=True,
                        verbose_name="Название подразделения",
                    ),
                ),
            ],
            options={
                "verbose_name": "Подразделение",
                "verbose_name_plural": "Подразделения",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Document",
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
                    "number",
                    models.CharField(
                        max_length=100,
                        unique=True,
                        verbose_name="Номер документа",
                    ),
                ),
            ],
            options={
                "verbose_name": "Документ",
                "verbose_name_plural": "Документы",
                "ordering": ["number"],
            },
        ),
    ]
