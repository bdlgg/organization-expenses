"""URL-маршруты справочников организации."""

from django.urls import path

from . import views

app_name = "catalogs"

urlpatterns = [
    path("categories/", views.categories_page, name="categories"),
    path("departments/", views.departments_page, name="departments"),
    path("documents/", views.documents_page, name="documents"),
]
