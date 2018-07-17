"""
Remote/offsite backup storage backend using Google Drive.

Auth is done through service accounts, see
https://developers.google.com/identity/protocols/OAuth2ServiceAccount
"""
import os
import tarfile

import googleapiclient.discovery
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload

from .. import BackupArchive, BackupTransfer, UploadError
from .base import Base


def sizeof_fmt(num, suffix='B'):
    # see https://stackoverflow.com/a/1094933/973537
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def make_tarfile(output_filename: str, source_dir: str) -> None:
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))
    assert os.path.exists(output_filename), "Archive creation (%s) failed" % output_filename


def pprint_key_value(mapping, formatter=None):
    for key, value in mapping.items():
        value = formatter(value) if formatter else value
        print(f"    {key}: {value}")


class Backend(Base):

    SCOPES = [
        'https://www.googleapis.com/auth/drive.file'
    ]

    _folder_id = None

    def __init__(self, client_secrets: str):
        """
        A remote backup transfer backend using Google Drive.

        :param client_secrets: (absolute) path to the client_secrets.json file
          containing the credentials to connect to the API. Note that a service
          account is required for non-interactive behaviour (and the only way
          implemented currently).
        """
        self.client_secrets = client_secrets

    # Backend
    @property
    def service(self):
        if not hasattr(self, '_service'):
            credentials = service_account.Credentials.from_service_account_file(
                self.client_secrets,
                scopes=self.SCOPES
            )

            self._service = googleapiclient.discovery.build('drive', 'v3', credentials=credentials)
        return self._service

    def show_quota(self):
        """
        Print the storage quota.
        """
        quota = self.service.about().get(fields='storageQuota').execute()['storageQuota']
        print("Quota:")
        pprint_key_value(quota, lambda x: sizeof_fmt(int(x)))

    def _get_or_create_dir(self, name, parent=None) -> str:
        # search if the folder exists
        search_q = "name='{}' and mimeType='application/vnd.google-apps.folder'".format(name)
        if parent:
            search_q += "and '{}' in parents".format(parent)
        else:
            search_q += "and 'root' in parents"

        folders = (
            self.service.files()
            .list(q=search_q, fields='files(id, parents)')
            .execute()
            .get('files', [])
        )
        if folders:
            return folders[0]['id']

        _folder = (
            self.service
            .files()
            .create(body={
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent] if parent else [],
            }, fields='id')
            .execute()
        )
        return _folder['id']

    def ensure_dirs(self, path: str):
        """
        Ensure the folders in path exist on Drive.
        """
        if path.startswith('/'):
            path = path[1:]
        if path.endswith('/'):
            path = path[:-1]

        folders = path.split('/')

        _folder_id = None
        for folder in folders:
            _folder_id = self._get_or_create_dir(folder, _folder_id)

        self._folder_id = _folder_id

    def prepare(self, full_path: str) -> BackupArchive:
        """
        Prepare the archive on the local drive.

        :param full_path: full path to the directory to archive
        :return: BackupArchive instance
        """
        output_filename = "{}.tar.gz".format(full_path)

        if not os.path.exists(output_filename):
            make_tarfile(output_filename, full_path)

        return BackupArchive(output_filename)

    def exists(self, backup_archive: BackupArchive) -> bool:
        """
        Check if the file exists on the remote
        """
        assert self._folder_id, "ensure_dirs() must be called before uploading files"

        name = os.path.basename(backup_archive.archive)
        search_q = (
            "name='{}' "
            "and mimeType='application/gzip' "
            "and '{}' in parents"
        ).format(name, self._folder_id)

        files = (
            self.service
            .files()
            .list(q=search_q, fields='files(md5Checksum)')
            .execute()
            .get('files', [])
        )
        if files:
            checksum = backup_archive.md5_checksum
            return any([
                file_['md5Checksum'] == checksum for file_ in files
            ])

        return False

    def upload(self, backup_archive):
        assert self._folder_id, "ensure_dirs() must be called before uploading files"
        file_name = os.path.basename(backup_archive.archive)
        metadata = {
            'name': file_name,
            'originalFilename': backup_archive.archive,
            'parents': [self._folder_id]
        }
        media = MediaFileUpload(backup_archive.archive, mimetype='application/gzip')

        response = (
            self.service
            .files()
            .create(
                body=metadata,
                media_body=media,
                fields='md5Checksum'
            )
            .execute()
        )

        if response['md5Checksum'] != backup_archive.md5_checksum:
            raise UploadError("Uploaded archive checksum does not match")

    # CLI extension
    @classmethod
    def add_arguments(cls, parser):
        BackendCli.add_arguments(parser)

    def handle_command(self, transfer, options) -> bool:
        return BackendCli.handle_command(transfer, options)

    def test_connection(self):
        user = self.service.about().get(fields='user').execute()['user']
        print("User:")
        pprint_key_value(user)

    def give_permissions(self, transfer: BackupTransfer, email: str):
        """
        Assign read permissions to the e-mail address.
        """
        bits = [bit for bit in transfer.config.transfer_path.split('/') if bit]
        folder_id = self._get_or_create_dir(bits[0], parent=None)

        self.service.permissions().create(
            fileId=folder_id,
            body={
                'type': 'user',
                'role': 'reader',
                'emailAddress': email,
            }
        ).execute()
        print("Folder {} can now be read".format(bits[0]))


class BackendCli:

    @staticmethod
    def add_arguments(parser):
        drive_parser = parser.add_subparsers(help='Google Drive commands', dest='drive_command')

        drive_parser.add_parser('test_connection', help="Test Google Drive connection/credentials")

        drive_parser.add_parser('show_quota', help="Show the Drive quota")

        give_permissions = drive_parser.add_parser('give_permissions', help="Give read permissions to a user")
        give_permissions.add_argument('email', help="E-mail address of user to get read permission")

    @staticmethod
    def handle_command(transfer, options) -> bool:
        subcommand = options.drive_command

        if not subcommand:
            return False

        if subcommand == 'give_permissions':
            transfer.backend.give_permissions(transfer, options.email)
        elif subcommand == 'test_connection':
            transfer.backend.test_connection()
        elif subcommand == 'show_quota':
            transfer.backend.show_quota()
        return True
