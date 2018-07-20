import json
import logging
import tarfile
from io import StringIO

import googleapiclient.discovery
import pytest
from apiclient.http import HttpMock, HttpMockSequence

from ctrl_z._cli import CLI
from ctrl_z.transfer import UploadError
from ctrl_z.transfer.backends.google_drive import Backend


class Service:
    _service = None

    @classmethod
    def get(cls):
        if not cls._service:
            # use the real discovery file - makes an actual HTTP request
            # this is a conscious decision - we don't want to be testing
            # against a no-longer functional discovery file
            cls._service = googleapiclient.discovery.build('drive', 'v3', developerKey='dummy')
        return cls._service


def _get_backend(response: dict=None, responses=None) -> Backend:
    logging.disable(logging.CRITICAL)
    backend = Backend('dummy')
    backend.stdout = StringIO()
    backend._service = Service.get()
    logging.disable(logging.NOTSET)

    # set the response data
    backend._http = HttpMock()
    if response:
        backend._http.data = json.dumps(response)

    elif responses:
        iterable = [
            ({'status': '200'}, json.dumps(response))
            for response in responses
        ]
        backend._http = HttpMockSequence(iterable)

    return backend


class CLIBackend(Backend):

    def __init__(self, response):
        logging.disable(logging.CRITICAL)
        self._service = Service.get()
        self._http = HttpMock()
        self._http.data = json.dumps(response)
        logging.disable(logging.NOTSET)

    def _get_or_create_dir(self, *args, **kwargs) -> str:
        return 'dummy'


def test_show_quota(capsys):
    backend = _get_backend(response={
        'storageQuota': {
            'limit': '16106127360',
            'usage': '13344214',
            'usageInDrive': '13344214',
            'usageInDriveTrash': '0'
        }
    })

    backend.show_quota()

    out = backend.stdout
    out.seek(0)
    assert out.read() == """Quota:
    limit: 15.0GiB
    usage: 12.7MiB
    usageInDrive: 12.7MiB
    usageInDriveTrash: 0.0B
"""


def test_prepare(tmpdir):
    """
    Test that the prepare method creates a tar.gz archive
    """
    tmpdir.join('some_file.sql').write("SELECT 1;")
    backend = _get_backend()

    archive = backend.prepare(str(tmpdir))

    with tarfile.open(archive.archive, 'r:gz') as arc:
        members = arc.getmembers()

    assert len(members) == 1
    assert members[0].name == 'some_file.sql'


@pytest.mark.parametrize("files,exists", [
    ([], False),
    ([{'md5Checksum': '5bd245d3a0f0183dcdf4ae4893bf1312'},
      {'md5Checksum': '865689b06759eb81cda2e0bcdf742d47'}], False),
])
def test_archive_doesnt_exists(tmpdir, files, exists):
    tmpdir.join('some_file.sql').write("SELECT 1;")
    backend = _get_backend(response={'files': files})
    backend._folder_id = 'dummy'

    archive = backend.prepare(str(tmpdir))
    assert backend.exists(archive) == exists


def test_archive_exists(tmpdir):
    tmpdir.join('some_file.sql').write("SELECT 1;")
    backend = _get_backend()
    backend._folder_id = 'dummy'

    archive = backend.prepare(str(tmpdir))
    backend._http.data = json.dumps({
        # need to use the actual checksum here, since gzip includes the timestamp
        # in the header
        'files': [{'md5Checksum': archive.md5_checksum}]
    })

    assert backend.exists(archive)


def test_upload_success(tmpdir):
    tmpdir.join('some_file.sql').write("SELECT 1;")
    backend = _get_backend()
    backend._folder_id = 'dummy'

    archive = backend.prepare(str(tmpdir))
    backend._http.data = json.dumps(
        # need to use the actual checksum here, since gzip includes the
        # timestamp in the header
        {'md5Checksum': archive.md5_checksum}
    )

    try:
        backend.upload(archive)
    except UploadError:
        pytest.fail("Upload should succeed when md5_checksums match")


def test_upload_fails(tmpdir):
    tmpdir.join('some_file.sql').write("SELECT 1;")
    backend = _get_backend({'md5Checksum': 'incorrect'})
    backend._folder_id = 'dummy'

    archive = backend.prepare(str(tmpdir))
    with pytest.raises(UploadError):
        backend.upload(archive)


def test_ensure_dirs_create():
    """
    Check that the directory structure is created in Drive.
    """
    backend = _get_backend(responses=[
        {
            'files': [],
        },
        {
            'id': 'dummy-123'
        }
    ])

    backend.ensure_dirs('/sub')

    assert backend._folder_id == 'dummy-123'


def test_ensure_dirs_exists():
    """
    Check that the directory structure is created in Drive.
    """
    backend = _get_backend(responses=[
        {
            'files': [{'id': 'dummy-123'}],
        },
    ])

    backend.ensure_dirs('/sub')

    assert backend._folder_id == 'dummy-123'


def test_cli_extension_test_connection(tmpdir, config_writer):
    config_path = str(tmpdir.join('config.yml'))
    backups_base = tmpdir.join('backups')

    config_writer(
        config_path,
        base_dir=str(backups_base),
        transfer_backend='tests.backends.test_google_drive.CLIBackend',
        transfer_backend_init_kwargs={'response': {
            'user': {
                'foo': 'bar'
            }
        }}
    )
    stdout = StringIO()
    cli = CLI()

    cli(['transfer', 'test_connection'], config_file=config_path, stdout=stdout)

    stdout.seek(0)
    assert stdout.read() == "User:\n    foo: bar\n"


def test_cli_extension_show_quota(tmpdir, config_writer):
    config_path = str(tmpdir.join('config.yml'))
    backups_base = tmpdir.join('backups')

    config_writer(
        config_path,
        base_dir=str(backups_base),
        transfer_backend='tests.backends.test_google_drive.CLIBackend',
        transfer_backend_init_kwargs={'response': {
            'storageQuota': {
                'limit': '16106127360',
                'usage': '13344214',
                'usageInDrive': '13344214',
                'usageInDriveTrash': '0'
            }
        }}
    )
    stdout = StringIO()
    cli = CLI()

    cli(['transfer', 'show_quota'], config_file=config_path, stdout=stdout)

    stdout.seek(0)
    assert stdout.read() == """Quota:
    limit: 15.0GiB
    usage: 12.7MiB
    usageInDrive: 12.7MiB
    usageInDriveTrash: 0.0B
"""


def test_cli_extension_give_permissions(tmpdir, config_writer):
    config_path = str(tmpdir.join('config.yml'))
    backups_base = tmpdir.join('backups')

    config_writer(
        config_path,
        base_dir=str(backups_base),
        transfer_backend='tests.backends.test_google_drive.CLIBackend',
        transfer_backend_init_kwargs={'response': {}},
        transfer_path='/root/sub/dir'
    )
    stdout = StringIO()
    cli = CLI()

    cli(
        ['transfer', 'give_permissions', 'hello@example.com'],
        config_file=config_path, stdout=stdout
    )

    stdout.seek(0)
    assert stdout.read() == 'Folder root can now be read\n'
