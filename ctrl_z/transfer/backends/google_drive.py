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

from .. import BackupArchive, UploadError


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


class Backend:

    SERVICE_ACCOUNT_FILE = '/home/bbt/code/isprojects/ispnext/backend/backup/client_secrets.json'

    SCOPES = [
        'https://www.googleapis.com/auth/drive.file'
    ]

    _folder_id = None

    @property
    def service(self):
        if not hasattr(self, '_service'):
            credentials = service_account.Credentials.from_service_account_file(
                self.SERVICE_ACCOUNT_FILE,
                scopes=self.SCOPES
            )

            self._service = googleapiclient.discovery.build('drive', 'v3', credentials=credentials)
        return self._service

    def show_quota(self):
        quota = self.service.about().get(fields='storageQuota').execute()['storageQuota']
        print("\nQuota:")
        for key, value in quota.items():
            size = sizeof_fmt(int(value))
            print(f"    {key}: {size}")
        print("\n")

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
