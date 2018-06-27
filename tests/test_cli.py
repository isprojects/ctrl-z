"""
Integration tests for the command line interface implementation.
"""
import argparse
import os
import sys
import warnings
from datetime import datetime
from io import StringIO

import pytest

from ctrl_z import cli
from ctrl_z.config import DEFAULT_CONFIG_FILE


def test_config_generation(config_path):
    cli(['generate_config'], stdout=StringIO(), config_file=config_path)

    cli.stdout.seek(0)
    result = cli.stdout.read()
    with open(DEFAULT_CONFIG_FILE, 'r') as default_config:
        assert result == default_config.read()


def test_config_generation_external_file(tmpdir, config_path):
    tempfile = str(tmpdir.join("some_config.yml"))

    cli(
        ['generate_config', '-o', tempfile],
        stdout=StringIO(), config_file=config_path
    )

    cli.stdout.seek(0)
    assert cli.stdout.read() == ''
    with open(DEFAULT_CONFIG_FILE, 'r') as default_config:
        with open(tempfile, 'r') as config:
            assert config.read() == default_config.read()


def test_full_backup(tmpdir, settings, config_writer):
    config_path = str(tmpdir.join('config.yml'))
    backups_base = tmpdir.join('backups')

    config_writer(config_path, base_dir=str(backups_base))

    # prevent actual db access
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=UserWarning)
        settings.DATABASES = {}
    settings.MEDIA_ROOT = str(tmpdir.join('media'))

    cli(args=['backup'], config_file=config_path, stdout=StringIO())

    expected_date = datetime.utcnow().strftime("%Y-%m-%d")

    # assert that the backup directory was created
    children = os.listdir(backups_base)
    assert len(children) == 1
    backup_dir = children[0]
    assert backup_dir.startswith(expected_date)

    full_path = backups_base.join(backup_dir)
    subdirs = os.listdir(full_path)
    assert sorted(subdirs) == ['backup.log', 'db', 'files']


def test_full_restore(tmpdir, settings, config_writer):
    config_path = str(tmpdir.join('config.yml'))
    backups_base = tmpdir.mkdir('backups')
    backup_dir = backups_base.mkdir('2018-05-29-daily')
    backup_dir.mkdir('db')
    backup_dir.mkdir('files')

    config_writer(config_path, base_dir=str(backups_base))

    # prevent actual db access
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=UserWarning)
        settings.DATABASES = {}
    settings.MEDIA_ROOT = str(tmpdir.join('media'))

    cli(args=['restore', str(backup_dir)], config_file=config_path, stdout=StringIO())

    # verify that the log file was created
    assert 'backup.log' in os.listdir(backup_dir)


def test_full_restore_bad_directory():
    with pytest.raises(argparse.ArgumentTypeError):
        cli(args=['restore', '/i/dont/exist/'], stdout=StringIO())


@pytest.mark.skipif(sys.platform == 'win32',
                    reason="does not run on windows")
def test_full_restore_bad_directory2(tmpdir):
    bad_permissions_dir = str(tmpdir.mkdir('nope'))
    os.chmod(bad_permissions_dir, 0o000)

    with pytest.raises(argparse.ArgumentTypeError):
        cli(args=['restore', bad_permissions_dir], stdout=StringIO())


def test_full_restore_not_directory(tmpdir):
    some_file = tmpdir.join('not_a_dir.txt')
    some_file.write("not a dir!\n")

    with pytest.raises(argparse.ArgumentTypeError):
        cli(args=['restore', str(some_file)], stdout=StringIO())
