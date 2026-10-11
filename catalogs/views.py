from pathlib import Path

from django.http import HttpResponse
from django.utils.html import escape

from homepage.views import page
from storage import load_categories, load_departments, load_documents

BASE_DIR = Path(__file__).resolve().parent.parent


def categories_page(request):
    """Показать категории расходов."""
    categories = load_categories(
        str(BASE_DIR / "data" / "categories.json")
    )
    items = "".join(
        f'<li class="list-group-item">{escape(category.name)}</li>'
        for category in categories
    )

    if not items:
        items = '<li class="list-group-item">Категорий пока нет.</li>'

    content = f"""
    <h1 class="mb-3">Категории расходов</h1>
    <ul class="list-group">{items}</ul>
    """

    return HttpResponse(page("Категории", content))


def departments_page(request):
    """Показать подразделения организации."""
    departments = load_departments(
        str(BASE_DIR / "data" / "departments.json")
    )
    items = "".join(
        f'<li class="list-group-item">{escape(department.name)}</li>'
        for department in departments
    )

    if not items:
        items = (
            '<li class="list-group-item">Подразделений пока нет.</li>'
        )

    content = f"""
    <h1 class="mb-3">Подразделения организации</h1>
    <ul class="list-group">{items}</ul>
    """

    return HttpResponse(page("Подразделения", content))


def documents_page(request):
    """Показать документы, связанные с расходами."""
    documents = load_documents(
        str(BASE_DIR / "data" / "documents.json")
    )
    items = "".join(
        f'<li class="list-group-item">{escape(document.number)}</li>'
        for document in documents
    )

    if not items:
        items = '<li class="list-group-item">Документов пока нет.</li>'

    content = f"""
    <h1 class="mb-3">Документы</h1>
    <ul class="list-group">{items}</ul>
    """

    return HttpResponse(page("Документы", content))
