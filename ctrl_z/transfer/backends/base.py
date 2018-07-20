import argparse

from .. import BackupArchive, BackupTransfer
from ..._cli import CLI


class Base:
    """
    Define the public API that a backend must implement.
    """

    def show_quota(self):
        raise NotImplementedError("Transfer backends must implement a show_quota() method")

    def ensure_dirs(self, path: str):
        """
        Ensure the folders in path exist on the remote.
        """
        pass

    def prepare(self, full_path: str) -> BackupArchive:
        """
        Prepare the archive on the local drive.

        :param full_path: full path to the directory to archive
        :return: BackupArchive instance
        """
        raise NotImplementedError("Transfer backends must implement a prepare() method")

    def exists(self, backup_archive: BackupArchive) -> bool:
        """
        Check if the file exists on the remote
        """
        raise NotImplementedError("Transfer backends must implement a exists() method")

    def upload(self, backup_archive):
        raise NotImplementedError("Transfer backends must implement a upload() method")

    @classmethod
    def add_arguments(cls, parser):
        """
        Add optional command line arguments.
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
