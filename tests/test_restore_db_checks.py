from io import StringIO

from django.core.management import call_command
from django.db import connection

import pytest

# aliased, otherwise it's picked up as a test function by pytest
from ctrl_z.db_restore import test_migrations_table as check_migrations


@pytest.mark.django_db
def test_non_migrated_db():
    defaults = {
        "interactive": False,
        "database": "secondary",
        "fake": True,
        "stdout": StringIO(),
    }
    call_command("migrate", "contenttypes", "zero", **defaults)

    assert check_migrations(using="secondary") is False


@pytest.mark.django_db
def test_migrated_db():
    assert check_migrations() is True


@pytest.mark.django_db
def test_table_does_not_exist():
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE django_migrations;")

    assert check_migrations() is False
