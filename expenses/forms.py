"""Формы фильтрации, создания, редактирования и обработки расходов."""

from decimal import Decimal

from django import forms
from PIL import Image, UnidentifiedImageError

from catalogs.models import Category, Department, Document
from .models import Expense


MAX_RECEIPT_IMAGE_SIZE = 5 * 1024 * 1024


class ExpenseFilterForm(forms.Form):
    """Проверить GET-параметры фильтрации реестра расходов."""

    min_amount = forms.DecimalField(
        required=False,
        min_value=Decimal("0.00"),
        max_digits=12,
        decimal_places=2,
        error_messages={"invalid": "Введите корректную сумму."},
        label="Сумма от, ₽",
        help_text="Показывать расходы не меньше указанной суммы.",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": "0",
                "step": "0.01",
                "placeholder": "0,00",
            }
        ),
    )
    category_id = forms.ModelChoiceField(
        queryset=Category.objects.order_by("name"),
        required=False,
        label="Категория",
        empty_label="Все категории",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    department_id = forms.ModelChoiceField(
        queryset=Department.objects.order_by("name"),
        required=False,
        label="Подразделение",
        empty_label="Все подразделения",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    q = forms.CharField(
        required=False,
        max_length=150,
        strip=True,
        label="Поиск",
        help_text=(
            "Поиск по категории, подразделению, документу и комментарию."
        ),
        widget=forms.SearchInput(
            attrs={
                "class": "form-control",
                "placeholder": "Что найти?",
            }
        ),
    )
    document = forms.CharField(
        required=False,
        max_length=100,
        strip=True,
        label="Номер документа",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Например, СЧ-101",
            }
        ),
    )
    sort = forms.ChoiceField(
        required=False,
        label="Сортировка",
        choices=(
            ("amount_desc", "Сначала большие суммы"),
            ("amount_asc", "Сначала маленькие суммы"),
            ("category", "По категории"),
            ("department", "По подразделению"),
        ),
        widget=forms.Select(attrs={"class": "form-select"}),
    )


class ExpenseForm(forms.ModelForm):
    """Создать расход или изменить разрешённые для пользователя поля."""

    class Meta:
        model = Expense
        # Статус и slug задаются приложением и не редактируются этой формой.
        fields = (
            "amount",
            "category",
            "department",
            "document",
            "comment",
            "receipt_image",
        )
        labels = {
            "amount": "Сумма расхода, ₽",
            "category": "Категория расходов",
            "department": "Подразделение организации",
            "document": "Подтверждающий документ",
            "comment": "Комментарий",
            "receipt_image": "Скан или фотография документа",
        }
        help_texts = {
            "amount": "Укажите положительную сумму с точностью до копеек.",
            "category": "Выберите статью, к которой относится расход.",
            "department": "Выберите подразделение, понёсшее расход.",
            "document": "Выберите документ из существующего справочника.",
            "comment": "Необязательное пояснение к операции.",
            "receipt_image": "Формат изображения: JPG, PNG или WebP; до 5 МБ.",
        }
        widgets = {
            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0.01",
                    "step": "0.01",
                    "placeholder": "0,00",
                }
            ),
            "category": forms.Select(attrs={"class": "form-select"}),
            "department": forms.Select(attrs={"class": "form-select"}),
            "document": forms.Select(attrs={"class": "form-select"}),
            "comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Например, оплата офисного оборудования",
                }
            ),
            "receipt_image": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/jpeg,image/png,image/webp",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        """Сортировать варианты выбора по названию/номеру."""
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.order_by("name")
        self.fields["department"].queryset = Department.objects.order_by(
            "name"
        )
        self.fields["document"].queryset = Document.objects.order_by("number")

    def clean_amount(self):
        """Не принимать нулевую или отрицательную сумму расхода."""
        amount = self.cleaned_data["amount"]
        if amount <= Decimal("0.00"):
            raise forms.ValidationError(
                "Сумма расхода должна быть больше нуля."
            )
        return amount

    def clean_receipt_image(self):
        """Ограничить размер загружаемого изображения документа."""
        image = self.cleaned_data.get("receipt_image")
        if image and image.size > MAX_RECEIPT_IMAGE_SIZE:
            raise forms.ValidationError(
                "Размер изображения не должен превышать 5 МБ."
            )

        if image:
            try:
                image.seek(0)
                with Image.open(image) as uploaded_image:
                    image_format = uploaded_image.format
            except (UnidentifiedImageError, OSError) as error:
                raise forms.ValidationError(
                    "Не удалось определить формат изображения."
                ) from error
            finally:
                image.seek(0)

            if image_format not in {"JPEG", "PNG", "WEBP"}:
                raise forms.ValidationError(
                    "Разрешены только изображения JPG, PNG и WebP."
                )

        return image


class ExpenseStatusForm(forms.Form):
    """Проверить допустимый переход статуса существующего расхода."""

    status = forms.ChoiceField(
        label="Новый статус",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    TRANSITIONS = {
        "PENDING": ("APPROVED", "CANCELLED"),
        "APPROVED": ("PAID", "CANCELLED"),
        "PAID": (),
        "CANCELLED": (),
    }

    def __init__(self, *args, expense, **kwargs):
        super().__init__(*args, **kwargs)
        allowed_statuses = self.TRANSITIONS.get(expense.status, ())
        labels = dict(Expense.STATUS_CHOICES)
        self.fields["status"].choices = [
            (value, labels[value]) for value in allowed_statuses
        ]
        self.fields["status"].help_text = (
            (
                "Статус можно изменить в соответствии "
                "с этапом обработки расхода."
            )
        )


class ExpenseThresholdForm(forms.Form):
    """Проверить порог суммы для выборки крупных расходов."""

    threshold = forms.DecimalField(
        required=True,
        min_value=Decimal("0.00"),
        max_digits=12,
        decimal_places=2,
        label="Порог суммы, ₽",
        error_messages={
            "invalid": "Введите корректную сумму.",
            "required": "Укажите порог суммы.",
        },
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": "0",
                "step": "0.01",
            }
        ),
    )
