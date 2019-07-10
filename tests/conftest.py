import os
import tempfile

from django.conf import settings

import pytest

from ctrl_z.config import DEFAULT_CONFIG_FILE, Config


def pytest_configure():
    settings.configure(
        SECRET_KEY="undo",
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "ctrlz",
                "USER": os.getenv("PGUSER", "ctrlz"),
                "PASSWORD": os.getenv("PGPASSWORD", "ctrlz"),
                "PORT": os.getenv("PGPORT", 5432),
            },
            "secondary": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "ctrlz2",
                "USER": os.getenv("PGUSER", "ctrlz"),
                "PASSWORD": os.getenv("PGPASSWORD", "ctrlz"),
                "PORT": os.getenv("PGPORT", 5432),
            },
        },
        MEDIA_ROOT=tempfile.mkdtemp(),
        INSTALLED_APPS=["django.contrib.contenttypes"],
    )


@pytest.fixture
def config_writer(tmpdir):
    def writer(path=None, **overrides):
        if "base_dir" not in overrides:
            overrides["base_dir"] = str(tmpdir.mkdir("backups"))
        if path is None:
            path = str(tmpdir.join("config.yml"))
        config = Config.from_file(DEFAULT_CONFIG_FILE, **overrides)
        config.write_to(path)

    return writer


@pytest.fixture
def config_path(tmpdir, config_writer):
    """
    Generate a config with a writable base.
    """
    config_path = str(tmpdir.join("config.yml"))
    backups_base = tmpdir.join("backups")
    config_writer(config_path, base_dir=str(backups_base))
    return config_path
