import logging

from django.db import connections
from django.db.utils import OperationalError, ProgrammingError

logger = logging.getLogger(__name__)


def test_migrations_table(using: str = "default") -> bool:
    """
    Use the django_migrations table to verify a backup restore.

    While this isn't foolproof, if there are no django_migrations entries (or
    the table does not exist), you can be sure that the restore failed.

    :param using: alias for the database, as in settings.DATABASES
    """
    connection = connections[using]
    try:
        with connection.cursor() as cursor:
            try:
                cursor.execute("SELECT COUNT(*) FROM django_migrations;")
            except ProgrammingError:
                logger.exception("Query failed")
                return False
            else:
                (count,) = cursor.fetchone()
    except OperationalError:
        logger.exception("Could not connect to database")
        return False

    return count > 0
