import os

from django.db import connection, connections

from ctrl_z import Backup

BACKUPS_DIR = os.path.join(os.path.dirname(__file__), 'backups')


def test_restore_db(tmpdir, config_writer, django_db_blocker):
    config_writer(base_dir=BACKUPS_DIR)
    backup = Backup.prepare_restore(
        str(tmpdir.join('config.yml')),
        os.path.join(BACKUPS_DIR, '2018-06-27-daily')
    )

    # uses the actual db name, not the test db name
    with django_db_blocker.unblock():
        with connection.cursor() as cursor:
            cursor.execute('DROP TABLE IF EXISTS django_migrations;')

        backup.restore(files=False)

        # check that the table is there
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM django_migrations;")
            (count,) = cursor.fetchone()

        assert count > 0


def test_skip_restore_alias(tmpdir, config_writer, django_db_blocker):
    config_writer(base_dir=BACKUPS_DIR)
    backup = Backup.prepare_restore(
        str(tmpdir.join('config.yml')),
        os.path.join(BACKUPS_DIR, '2018-06-27-daily')
    )

    # uses the actual db name, not the test db name
    with django_db_blocker.unblock():
        with connections['default'].cursor() as cursor:
            cursor.execute('DROP TABLE IF EXISTS django_migrations;')

        with connections['secondary'].cursor() as cursor:
            cursor.execute('DROP TABLE IF EXISTS django_migrations;')

        backup.restore(files=False, skip_db='secondary')

        with connections['default'].cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM django_migrations;")
            (count,) = cursor.fetchone()
            assert count > 0

        with connections['secondary'].cursor() as cursor:
            sql = """
                SELECT EXISTS (
                   SELECT 1
                   FROM   information_schema.tables
                   WHERE  table_schema = 'public'
                   AND    table_name = 'django_migrations'
                );
            """
            cursor.execute(sql)
            (exists,) = cursor.fetchone()

            assert not exists
