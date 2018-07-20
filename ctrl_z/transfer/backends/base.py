import argparse

from .. import BackupArchive, BackupTransfer
from ..._cli import CLI


class Base:
    """
    Define the public API that a backend must implement.
    """

    def show_quota(self):
        """
        Show information about remote storage quota.
        """
        raise NotImplementedError("Transfer backends must implement a show_quota() method")

    def ensure_dirs(self, path: str):
        """
        Ensure the folders in path exist on the remote.

        :param path: the path to the base directory on the remote. Folder names
          are separated by forward slashes, e.g. /var/backups/staging
        """
        pass

    def prepare(self, full_path: str) -> BackupArchive:
        """
        Prepare the archive on the local drive for upload/check.

        :param full_path: full path of the directory to archive
        :return: BackupArchive instance
        """
        raise NotImplementedError("Transfer backends must implement a prepare() method")

    def exists(self, backup_archive: BackupArchive) -> bool:
        """
        Check if the file exists on the remote
        """
        raise NotImplementedError("Transfer backends must implement a exists() method")

    def upload(self, backup_archive):
        """
        Upload the prepared archive to the remote

        :raises UploadError: if the integrity check failed, a
          :class:`ctrl_z.transfer.UploadError` should be raised.
        """
        raise NotImplementedError("Transfer backends must implement a upload() method")

    @classmethod
    def add_arguments(cls, parser):
        """
        Add optional command line arguments to extend the CLI.

        You may want to facilitate interacting with the remote through the CLI.

        :param parser: the ``transfer`` subparser of the main CLI, this is an
          argparse parser.
        """
        pass

    def handle_command(self, cli: CLI, transfer: BackupTransfer, options: argparse.Namespace) -> bool:
        """
        Handle backend specific commands

        :param cli: the CLI instance asking to handle the command
        :param transfer: the :class:`ctrl_z.transfer.BackupTransfer` instance
          holding the config.
        :param options: the CLI arguments parsed into argparse.Namespace
        :return: boolean indicating if a command was handled or not, if not,
          the default behaviour is to transfer the backup.
        """
        return False
