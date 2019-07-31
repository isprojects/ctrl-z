import os

from django.db import connection, connections

import pytest

from ctrl_z import Backup
from ctrl_z.backup import BackupError

BACKUPS_DIR = os.path.join(os.path.dirname(__file__), "backups")


def test_restore_db(tmpdir, config_writer, django_db_blocker):
    config_writer(base_dir=BACKUPS_DIR)
    backup = Backup.prepare_restore(
        str(tmpdir.join("config.yml")), os.path.join(BACKUPS_DIR, "2018-06-27-daily")
    )

    # uses the actual db name, not the test db name
    with django_db_blocker.unblock():
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS django_migrations;")

        backup.restore(files=False)

        # check that the table is there
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM django_migrations;")
            (count,) = cursor.fetchone()

        assert count > 0


def test_restore_different_db_name_host_port(
    tmpdir, config_writer, django_db_blocker, settings
):
    """
    Test that the database can be restored into a different database name.

    The dump archive contains the name of the source database, but there
    are scenarious where you want to restore into a different database than
    the source db name.
    """
    config_writer(base_dir=BACKUPS_DIR)
    backup = Backup.prepare_restore(
        str(tmpdir.join("config.yml")), os.path.join(BACKUPS_DIR, "2018-06-27-daily")
    )
    with django_db_blocker.unblock():

        backup.restore(
            files=False,
            skip_db=["secondary", "dummy"],
            db_names={"default": "dummy"},
            db_hosts={"default": "otherhost"},
            db_ports={"default": "5434"},
        )

        # check that the db & table is there
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM django_migrations;")
            (count,) = cursor.fetchone()

        assert count > 0


def test_skip_restore_alias(tmpdir, config_writer, django_db_blocker):
    config_writer(base_dir=BACKUPS_DIR)
    backup = Backup.prepare_restore(
        str(tmpdir.join("config.yml")), os.path.join(BACKUPS_DIR, "2018-06-27-daily")
    )

    # uses the actual db name, not the test db name
    with django_db_blocker.unblock():
        with connections["default"].cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS django_migrations;")

        with connections["secondary"].cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS django_migrations;")

        backup.restore(files=False, skip_db=["secondary"])

        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM django_migrations;")
            (count,) = cursor.fetchone()
            assert count > 0

        with connections["secondary"].cursor() as cursor:
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


def test_restore_hard_failure(tmpdir, config_writer, django_db_blocker):
    config_writer(base_dir=BACKUPS_DIR)
    backup = Backup.prepare_restore(
        str(tmpdir.join("config.yml")),
        os.path.join(BACKUPS_DIR, "2018-06-26-daily"),  # doesn't exist
    )

    # uses the actual db name, not the test db name
    with django_db_blocker.unblock():
        with pytest.raises(BackupError):
            backup.restore(files=False)


def test_restore_folders(settings, tmpdir, config_writer):
    """
    Assert that uploaded file directories can be restored.
    """
    settings.MEDIA_ROOT = str(tmpdir.join("media"))
    settings.PRIVATE_MEDIA_ROOT = str(tmpdir.join("private_media"))

    config_writer(
        base_dir=BACKUPS_DIR,
        files={"directories": ["MEDIA_ROOT", "PRIVATE_MEDIA_ROOT"]},
    )

    backup = Backup.prepare_restore(
        str(tmpdir.join("config.yml")), os.path.join(BACKUPS_DIR, "2018-06-27-daily")
    )

    backup.restore(db=False)

    dirs = {local.basename for local in tmpdir.listdir() if local.isdir()}
    assert dirs == {"media", "private_media"}

    media_files = {item.basename for item in tmpdir.join("media").listdir()}
    assert media_files == {"1"}

    private_media_files = {
        item.basename for item in tmpdir.join("private_media").listdir()
    }
    assert private_media_files == {"2"}


def test_restore_folders_directories_setting(settings, tmpdir, config_writer):
    """
    Assert that uploaded file directories can be restored.
    """
    settings.MEDIA_ROOT = str(tmpdir.join("media"))
    settings.PRIVATE_MEDIA_ROOT = str(tmpdir.join("private_media"))

    config_writer(base_dir=BACKUPS_DIR, files={"directories": ["PRIVATE_MEDIA_ROOT"]})

    backup = Backup.prepare_restore(
        str(tmpdir.join("config.yml")), os.path.join(BACKUPS_DIR, "2018-06-27-daily")
    )

    backup.restore(db=False)

    dirs = {local.basename for local in tmpdir.listdir() if local.isdir()}
    assert dirs == {"private_media"}

    private_media_files = {
        item.basename for item in tmpdir.join("private_media").listdir()
    }
    assert private_media_files == {"2"}
