"""URL-маршруты приложения учёта расходов."""

from django.urls import path

from . import views

app_name = "expenses"

urlpatterns = [
    path("", views.expense_list, name="expense_list"),
    path("statistics/", views.expense_statistics, name="expense_statistics"),
    path("<int:expense_id>/", views.expense_detail, name="expense_detail"),
]
