"""Общая настройка Django для тестирования веб-представлений через pytest."""

import os
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "org_expenses.settings")

import django  # noqa: E402

django.setup()
