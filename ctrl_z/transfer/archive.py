import hashlib
import os


class BackupArchive:
    def __init__(self, archive: str):
        """
        A single backup as an archive.

        The archive format depends on the backend, it could be tar.gz, zip...

        :param archive: full path to the archive file
        """
        self.archive = archive

    @property
    def md5_checksum(self):
        """
        Calculate the md5 checksum of the archive
        """
        assert os.path.isfile(self.archive), "%s is not a file"
        hash_md5 = hashlib.md5()
        with open(self.archive, "rb") as archive:
            for chunk in iter(lambda: archive.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
