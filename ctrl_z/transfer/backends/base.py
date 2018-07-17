from .. import BackupArchive


class Base:

    def show_quota(self):
        raise NotImplementedError  # noqa

    def ensure_dirs(self):
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
        raise NotImplementedError  # noqa

    def exists(self, backup_archive: BackupArchive) -> bool:
        """
        Check if the file exists on the remote
        """
        raise NotImplementedError  # noqa

    def upload(self, backup_archive):
        raise NotImplementedError  # noqa

    @classmethod
    def add_arguments(cls, parser):
        """
        Add optional command line arguments.
        """
        pass

    def handle_command(self, options) -> bool:
        """
        Handle backend specific commands

        :return: boolean indicating if a command was handled or not, if not,
        the default behaviour is to transfer the backup.
        """
        return False
