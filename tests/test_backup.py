import logging
import os

from ctrl_z import Backup


def test_backup_no_db(tmpdir, settings, config_writer):
    settings.MEDIA_ROOT = str(tmpdir.mkdir("media"))

    tmpdir.join("media", "some_file.txt").write("to check")

    config_writer()
    backup = Backup.from_config(str(tmpdir.join("config.yml")))

    backup.full(db=False, files=True)

    backup_dir = tmpdir.join("backups").listdir()[0]
    media_file = backup_dir.join("files", "media", "some_file.txt")
    assert media_file.read() == "to check"

    # expected no database
    assert backup_dir.join("db").listdir() == []


def test_backup_files_skip_directory(tmpdir, settings, config_writer, caplog):
    """
    Assert that non existing directory is skipped
    """
    settings.MEDIA_ROOT = str(tmpdir.mkdir("media"))
    settings.NON_EXISTING_DIR = "NON_EXISTING_DIR"

    config_writer(files={"directories": ["MEDIA_ROOT", "NON_EXISTING_DIR"], "overwrite_existing_directory": "yes"},)
    backup = Backup.from_config(str(tmpdir.join("config.yml")))

    with caplog.at_level(logging.DEBUG):
        backup.full(db=False, files=True)

    assert "Source directory NON_EXISTING_DIR does not exist, skipping" in caplog.text


def test_backup_files_overwrite_target(tmpdir, settings, config_writer):
    settings.MEDIA_ROOT = str(tmpdir.mkdir("media"))

    tmpdir.join("media", "some_file.txt").write("to check")

    config_writer()
    backup = Backup.from_config(str(tmpdir.join("config.yml")))

    media_backup = os.path.join(backup.config.base_dir, "files", "media")
    os.makedirs(media_backup)

    with open(os.path.join(media_backup, "other_file.txt"), "w") as _other:
        _other.write("to overwrite")

    backup.full(db=False, files=True)

    backup_dir = tmpdir.join("backups").listdir()[0]
    assert len(backup_dir.join("files", "media").listdir()) == 1


def test_backup_skip_db(tmpdir, settings, config_writer):
    config_writer()
    backup = Backup.from_config(str(tmpdir.join("config.yml")))

    backup.full(db=True, skip_db=["default"], files=False)

    backup_dir = tmpdir.join("backups").listdir()[0]
    filenames = [item.basename for item in backup_dir.join("db").listdir()]

    port = settings.DATABASES["secondary"]["PORT"]
    assert filenames == ["localhost.{port}.test_ctrlz2.custom".format(port=port)]


def test_backup_all_db(tmpdir, settings, config_writer):
    config_writer()
    backup = Backup.from_config(str(tmpdir.join("config.yml")))

    backup.full(db=True, files=False)

    backup_dir = tmpdir.join("backups").listdir()[0]
    filenames = [item.basename for item in backup_dir.join("db").listdir()]

    port1 = settings.DATABASES["default"]["PORT"]
    port2 = settings.DATABASES["secondary"]["PORT"]
    assert set(filenames) == {
        "localhost.{port1}.test_ctrlz2.custom".format(port1=port1),
        "localhost.{port2}.test_ctrlz.custom".format(port2=port2),
    }


def test_backup_db_version_file(tmpdir, settings, config_writer):
    config_writer()
    backup = Backup.from_config(str(tmpdir.join("config.yml")))

    backup.full(db=True, files=False, version="TEST")

    backup_dir = tmpdir.join("backups").listdir()[0]
    version_dir = backup_dir.listdir()[0]
    assert version_dir.basename == "version"
    version_file = version_dir.listdir()[0]
    assert version_file.basename == "TEST.txt" 
    assert version_file.readlines() == ["TEST"]
    filenames = [item.basename for item in backup_dir.join("db").listdir()]
    port = settings.DATABASES["secondary"]["PORT"]
    assert filenames == ["localhost.{port}.test_ctrlz2.custom".format(port=port)]

