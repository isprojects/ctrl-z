import pytest

from ctrl_z.config import DEFAULT_CONFIG_FILE
from ctrl_z.transfer import BackupArchive, BackupTransfer, UploadError
from ctrl_z.transfer.backends import Base


def test_public_api(tmpdir):
    """
    Test that the base backend performs the appropriate checks for subclasses.
    """
    base_dir = tmpdir.mkdir('backups')
    base_dir.mkdir('2018-07-17-daily')

    transfer = BackupTransfer.from_config(DEFAULT_CONFIG_FILE, base_dir=str(base_dir))

    with pytest.raises(NotImplementedError):
        transfer.show_info()

    with pytest.raises(NotImplementedError):
        transfer.sync_to_remote()


class DummyBackend(Base):

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def exists(self, *args, **kwargs):
        return True

    def prepare(self, full_path: str) -> BackupArchive:
        return BackupArchive(full_path)

    def upload(self, archive):
        raise AssertionError("No uploads should happen if there are no backups")


def test_load_backend_from_settings():
    transfer = BackupTransfer.from_config(
        DEFAULT_CONFIG_FILE,
        transfer_backend='tests.test_transfer.DummyBackend',
        transfer_backend_init_kwargs={'foo': 'bar'}
    )

    assert isinstance(transfer.backend, DummyBackend)
    assert transfer.backend.kwargs == {'foo': 'bar'}


def test_sync_nothing_to_sync(tmpdir):
    """
    Test that the backend is not called if there's nothing to sync.
    """
    base_dir = tmpdir.mkdir('backups')
    # create some files that should be ignored
    base_dir.join('2018-07-17-daily').write('not a directory')
    base_dir.mkdir('ignore-me')

    transfer = BackupTransfer.from_config(
        DEFAULT_CONFIG_FILE,
        base_dir=str(base_dir),
        transfer_backend='tests.test_transfer.DummyBackend',
    )

    try:
        transfer.sync_to_remote()
    except AssertionError:
        pytest.fail("Upload should NOT have been called")


def test_sync_skip_existing(tmpdir):
    base_dir = tmpdir.mkdir('backups')
    base_dir.mkdir('2018-07-17-daily')

    transfer = BackupTransfer.from_config(
        DEFAULT_CONFIG_FILE,
        base_dir=str(base_dir),
        transfer_backend='tests.test_transfer.DummyBackend',
    )

    try:
        transfer.sync_to_remote()
    except AssertionError:
        pytest.fail("Upload should NOT have been called")


def test_upload_fails_continue_others(tmpdir, mocker):
    base_dir = tmpdir.mkdir('backups')
    base_dir.mkdir('2018-07-17-daily')
    base_dir.mkdir('2018-07-18-daily')

    transfer = BackupTransfer.from_config(
        DEFAULT_CONFIG_FILE,
        base_dir=str(base_dir),
        transfer_backend='tests.test_transfer.DummyBackend',
    )

    def side_effect(archive):
        if archive.archive.endswith('2018-07-17-daily'):
            raise UploadError("'Random' failure")
        else:
            pass

    mocker.patch.object(transfer.backend, 'exists', return_value=False)
    mock_upload = mocker.patch.object(transfer.backend, 'upload', side_effect=side_effect)

    with pytest.raises(UploadError):
        transfer.sync_to_remote()

    assert mock_upload.call_count == 2
