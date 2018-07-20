import logging
import os

from django.utils.module_loading import import_string

from ..config import Config
from ..utils import is_backup_dir

logger = logging.getLogger(__name__)


class UploadError(Exception):
    pass


class BackupTransfer:

    def __init__(self, config: Config):
        self.config = config

        cls = import_string(config.transfer_backend)
        self.backend = cls(**config.transfer_backend_init_kwargs)

    @classmethod
    def from_config(cls, config_file, **overrides):
        overrides['use_parent_dir'] = True
        config = Config.from_file(config_file, **overrides)
        return cls(config=config)

    def show_info(self):
        """
        Inventarize the operations to be done.
        """
        self.backend.show_quota()

    def sync_to_remote(self):
        """
        Transfer the backups to the remote.
        """
        logger.info("Scanning %s for backups to transfer...", self.config.base_dir)

        backup_dirs = []

        for dirname in sorted(os.listdir(self.config.base_dir)):
            full_path = os.path.join(self.config.base_dir, dirname)
            if not os.path.isdir(full_path):
                continue
            if not is_backup_dir(dirname):
                continue
            backup_dirs.append(dirname)

        # make sure the (relative) directory structure exists on the remote
        # this depends on the backend - for rsync for example this may not be
        # needed as it creates them on the fly
        self.backend.ensure_dirs(self.config.transfer_path)

        logger.info("Syncing backups %s to remote...", backup_dirs)

        has_failures = False
        for dirname in backup_dirs:
            full_path = os.path.join(self.config.base_dir, dirname)
            backup_archive = self.backend.prepare(full_path)
            if self.backend.exists(backup_archive):
                logger.info("Backup %s exists on remote, skipping", dirname)
                continue

            logger.info("Uploading %s to remote...", dirname)
            try:
                self.backend.upload(backup_archive)
            except UploadError:
                logger.exception("%s upload failed", dirname)
                has_failures = True
                continue
            logger.info("Uploaded %s to remote", dirname)

        if not has_failures:
            logger.info("Done syncing backups to remote")
        else:
            raise UploadError("Some backups failed to upload, check the error log")
