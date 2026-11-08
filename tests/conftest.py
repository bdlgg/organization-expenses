"""Настройка Django и тестовой SQLite-базы для pytest."""

import os
from pathlib import Path

import pytest

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in os.sys.path:
    os.sys.path.insert(0, str(PROJECT_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "org_expenses.settings")

import django  # noqa: E402

django.setup()


@pytest.fixture(scope="session", autouse=True)
def django_test_database():
    """Создать отдельную тестовую БД и применить к ней миграции Django."""
    from django.test.runner import DiscoverRunner

    runner = DiscoverRunner(verbosity=0, interactive=False)
    runner.setup_test_environment()
    old_config = runner.setup_databases()

    yield

    runner.teardown_databases(old_config)
    runner.teardown_test_environment()
