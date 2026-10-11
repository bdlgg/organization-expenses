from django.http import HttpResponse
from django.utils.html import escape


def page(title: str, content: str) -> str:
    """Собрать общий HTML-каркас всех страниц приложения."""
    bootstrap_css = (
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/"
        "dist/css/bootstrap.min.css"
    )
    safe_title = escape(title)

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{safe_title}</title>
    <link rel="stylesheet" href="{bootstrap_css}">
    <style>
        body {{ background: #f6f7f9; color: #212529; }}
        main {{ min-height: 70vh; }}
        .page-panel {{ background: #fff; border: 1px solid #dee2e6; }}
        .navbar-brand {{ font-weight: 600; }}
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg bg-white border-bottom">
        <div class="container py-2">
            <a class="navbar-brand" href="/">Учёт расходов</a>
            <div class="navbar-nav flex-row flex-wrap gap-2">
                <a class="nav-link" href="/expenses/">Расходы</a>
                <a class="nav-link" href="/categories/">Категории</a>
                <a class="nav-link" href="/departments/">Подразделения</a>
                <a class="nav-link" href="/documents/">Документы</a>
            </div>
        </div>
    </nav>
    <main class="container py-4">
        {content}
    </main>
    <footer class="container py-3 border-top text-secondary small">
        Система учета расходов организации · ПР5 · Django
    </footer>
</body>
</html>"""


def index(request):
    """Главная страница приложения."""
    content = """
    <section class="page-panel p-4 p-md-5 mb-4">
        <h1 class="display-6">Система учета расходов организации</h1>
        <p class="lead">
            Просмотр расходов, категорий, подразделений и документов.
        </p>
        <p>
            Веб-интерфейс использует объектную модель и JSON-хранилище,
            разработанные в предыдущих практических работах.
        </p>
        <a class="btn btn-dark me-2" href="/expenses/">
            Перейти к расходам
        </a>
        <a class="btn btn-outline-secondary" href="/categories/">
            Справочники
        </a>
    </section>
    <section class="row g-3">
        <div class="col-md-4">
            <div class="page-panel p-3 h-100">
                <h2 class="h5">Расходы</h2>
                <p class="mb-0">Список и подробная информация о расходе.</p>
            </div>
        </div>
        <div class="col-md-4">
            <div class="page-panel p-3 h-100">
                <h2 class="h5">Категории и подразделения</h2>
                <p class="mb-0">Справочная информация об учёте расходов.</p>
            </div>
        </div>
        <div class="col-md-4">
            <div class="page-panel p-3 h-100">
                <h2 class="h5">Документы</h2>
                <p class="mb-0">Документы, связанные с расходами.</p>
            </div>
        </div>
    </section>
    """
    return HttpResponse(page("Главная", content))


def page_not_found(request, exception):
    """Вернуть оформленную страницу 404 для неизвестного URL."""
    content = """
    <section class="page-panel p-4">
        <h1 class="text-danger">404 — страница не найдена</h1>
        <p>Проверьте адрес или вернитесь на главную страницу.</p>
        <a class="btn btn-dark" href="/">На главную</a>
    </section>
    """
    return HttpResponse(
        page("404 — страница не найдена", content),
        status=404,
    )
