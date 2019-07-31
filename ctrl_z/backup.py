import logging
import os
import shutil
import subprocess
from datetime import datetime
from typing import List, Optional

from django.conf import settings
from django.core.mail import send_mail
from django.utils.module_loading import import_string

from .config import Config

logger = logging.getLogger(__name__)


class BackupError(Exception):
    pass


class Backup:
    def __init__(self, config: Config, restore=False):
        self.config = config

        self.base_dir = self.config.base_dir
        self.db_dir = os.path.join(self.base_dir, "db")
        self.files_dir = os.path.join(self.base_dir, "files")

    @classmethod
    def from_config(cls, config_file):
        config = Config.from_file(config_file)
        return cls(config=config)

    @classmethod
    def prepare_restore(cls, config_file, base_dir: str):
        config = Config.from_file(config_file, base_dir=base_dir, restore=True)
        return cls(config=config)

    def restore(
        self,
        db=True,
        skip_db: Optional[List[str]] = None,
        files=True,
        db_names: Optional[dict] = None,
        db_hosts: Optional[dict] = None,
        db_ports: Optional[dict] = None,
    ):
        logger.info("Starting restore of %s", self.base_dir)

        if files:
            self.restore_files()
        if db:
            self.restore_databases(
                skip_db=skip_db, db_names=db_names, db_hosts=db_hosts, db_ports=db_ports
            )

        logger.info("Finished restore of %s", self.base_dir)

    def create_directories(self):
        logger.debug("Checking/creating folder tree for backups")

        paths = (self.db_dir, self.files_dir)
        for path in paths:
            if os.path.exists(path):
                if not os.path.isdir(path):
                    raise BackupError("Path %s exists, but is not a directory!" % path)
                continue

            logger.debug("Creating directory %s", path)
            os.makedirs(path)

    def full(self, db=True, skip_db=None, files=True):
        """
        Run all the components of the full backup.

        :param db: whether to backup database(s) or not
        :param skip_db: if backing up databases, aliases of the db's NOT to
          backup
        :param files: whether to backup (uploaded) files or not
        """
        logger.info("Performing full backup")
        self.rotate()
        self.create_directories()
        if db:
            self.databases(skip_db=skip_db)
        if files:
            self.files()
        logger.info("Full backup completed")

    def report(self, has_errors: bool):
        """
        Report on the success or failure of the backup.
        """
        if not self.config.report["enabled"]:
            logger.info("Report not enabled, aborting")
            return

        recipients = self.config.report["to"]

        logger.info("Sending report to %s", recipients)

        with open(
            os.path.join(self.base_dir, self.config.logging["filename"]), "r"
        ) as logfile:
            log_content = logfile.read()

        now = datetime.utcnow()
        subject_template = (
            "Backup {now} failed" if has_errors else "Backup {now} succeeded"
        )
        subject = subject_template.format(now=now)
        send_mail(subject, log_content, settings.DEFAULT_FROM_EMAIL, recipients)

    def databases(self, skip_db=None):
        """
        Backup all the databases used.

        :param skip_db: list of db aliases to skip
        """
        logger.info("Backing up %d databases", len(settings.DATABASES))
        for alias, db_config in settings.DATABASES.items():
            if skip_db and alias in skip_db:
                continue
            self._backup_database(db_config)

    def restore_databases(
        self,
        skip_db: Optional[List[str]],
        db_names: Optional[dict] = None,
        db_hosts: Optional[dict] = None,
        db_ports: Optional[dict] = None,
    ):
        logger.info("Restoring %d databases", len(settings.DATABASES))
        for alias, db_config in settings.DATABASES.items():
            if skip_db and alias in skip_db:
                continue
            source_db_name = db_names.get(alias) if db_names else None
            source_db_host = db_hosts.get(alias) if db_hosts else None
            source_db_port = db_ports.get(alias) if db_ports else None
            self._restore_database(
                alias,
                db_config,
                source_db_name=source_db_name,
                source_db_host=source_db_host,
                source_db_port=source_db_port,
            )

    def files(self):
        """
        Process all the 'uploaded' files.
        """
        directories = self._get_file_directories()
        logger.info("Backing up %d directories", len(directories))
        for directory in directories:
            self._backup_directory(directory)

    def restore_files(self):
        directories = self._get_file_directories()
        logger.info("Restoring %d directories...", len(directories))
        for path in directories:
            self._restore_directory(path)

    def _get_file_directories(self) -> list:
        directories = [
            getattr(settings, setting) for setting in self.config.files["directories"]
        ]
        return directories

    def rotate(self):
        """
        Rotate the existing backups according to the retention policy.
        """
        logger.info("Rotating backups")
        rotate_base = os.path.dirname(self.config.base_dir)
        self.config.retention_policy.rotate(rotate_base)

    def _get_conn_params(self, db_config: dict) -> tuple:
        host = db_config.get("HOST", "") or "localhost"
        port = db_config.get("PORT", "") or 5432
        name = db_config["NAME"]
        return host, port, name

    def _get_db_filename(self, db_config: dict) -> str:
        host, port, name = self._get_conn_params(db_config)
        return "{host}.{port}.{name}.custom".format(host=host, port=port, name=name)

    def _backup_database(self, db_config: dict):
        program = self.config.pg_dump_binary
        host, port, name = self._get_conn_params(db_config)
        filename = self._get_db_filename(db_config)
        outfile = os.path.join(self.db_dir, filename)

        args = [
            program,
            "-Fc",  # custom format, guaranteed that it can be loaded in newer Postgres versions
            "-f{outfile}".format(outfile=outfile),
        ]

        logger.info("Dumping database %s (%s:%s)", name, host, port)

        env = os.environ.copy()
        env.update(
            {
                "PGHOST": host,
                "PGPORT": str(port),
                "PGPASSWORD": db_config["PASSWORD"],
                "PGUSER": db_config["USER"],
                "PGDATABASE": name,
            }
        )

        process = subprocess.Popen(
            args, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        (stdout, stderr) = process.communicate()

        if stdout:
            logger.info("stdout: %s", stdout.decode())

        if stderr:
            logger.info("stderr: %s", stderr.decode())
            raise BackupError(stderr)

        logger.info("Database backup saved to %s", outfile)

    def _restore_database(
        self,
        alias: str,
        db_config: dict,
        source_db_name: Optional[str] = None,
        source_db_host: Optional[str] = None,
        source_db_port: Optional[str] = None,
    ):
        program = self.config.pg_restore_binary

        source_db_config = db_config.copy()
        if source_db_name:
            source_db_config["NAME"] = source_db_name
        if source_db_host:
            source_db_config["HOST"] = source_db_host
        if source_db_port:
            source_db_config["PORT"] = source_db_port

        host, port, name = self._get_conn_params(db_config)
        filename = self._get_db_filename(source_db_config)
        backup_file = os.path.join(self.db_dir, filename)

        if not os.path.isfile(backup_file):
            raise BackupError(
                "Dump file '{backup_file}' does not exist. Possibly you need "
                "to provide the alias mapping if you're restoring to a "
                "different database name.".format(backup_file=backup_file)
            )

        dropdb_args = [self.config.dropdb_binary, "--if-exists", db_config["NAME"]]

        createdb_args = [self.config.createdb_binary, db_config["NAME"]]

        args = [program, "-d%s" % db_config["NAME"], backup_file]

        logger.info("Restoring database %s (%s:%s)", name, host, port)

        env = os.environ.copy()
        env.update(
            {
                "PGHOST": host,
                "PGPORT": str(port),
                "PGPASSWORD": db_config["PASSWORD"],
                "PGUSER": db_config["USER"],
                "PGDATABASE": name,
            }
        )

        logger.info("Dropping the target database, if it exists")
        process = subprocess.Popen(
            dropdb_args, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        (stdout, stderr) = process.communicate()

        if stdout:  # noqa
            logger.info("stdout: %s", stdout.decode())

        if stderr:  # noqa
            logger.info("stderr: %s", stderr.decode())

        logger.info("Creating the target database")
        process = subprocess.Popen(
            createdb_args, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        (stdout, stderr) = process.communicate()

        if stdout:  # noqa
            logger.info("stdout: %s", stdout.decode())

        if stderr:  # noqa
            logger.info("stderr: %s", stderr.decode())

        logger.info("Restoring the target database")
        process = subprocess.Popen(
            args, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        (stdout, stderr) = process.communicate()

        if stdout:
            logger.info("stdout: %s", stdout.decode())

        if stderr:
            logger.info("stderr: %s", stderr.decode())

        # test if the restore was okay
        test_function = import_string(self.config.database["test_function"])
        if not test_function(alias):
            raise BackupError("Restore of '%s' database failed" % name)

        logger.info("Database backup %s restored", backup_file)

    def _backup_directory(self, directory: str):
        overwrite_existing = self.config.files["overwrite_existing_directory"]

        dirname = os.path.basename(directory)
        dest = os.path.join(self.files_dir, dirname)

        logger.info("Backing up %s to %s", directory, dest)

        if os.path.exists(dest):
            logger.debug(
                "Target destination exists, which conflicts with shutil.copytree"
            )
            if overwrite_existing:
                logger.info("Replacing %s", dest)
                shutil.rmtree(dest)
            else:
                logger.info("Skipping %s", dest)
                return

        if not os.path.exists(directory):
            logger.info("Source directory %s does not exist, skipping", directory)
            return

        shutil.copytree(directory, dest)

        logger.info("Backed up %s to %s", directory, dest)

    def _restore_directory(self, dest: str):
        dirname = os.path.basename(dest)
        src = os.path.join(self.files_dir, dirname)
        if not os.path.exists(src):
            logger.info("Not restoring %s - directory doesn't exist!", src)
            return

        logger.info("Restoring %s to %s", src, dest)

        if os.path.exists(dest):
            logger.debug("Target destination exists, removing...")

            # in a docker context, with directories mounted, the root node
            # cannot be deleted, so we delete all child nodes instead
            try:
                shutil.rmtree(dest)
            except OSError:
                for item in os.listdir(dest):
                    full_path = os.path.join(dest, item)
                    if os.path.isdir(full_path):
                        shutil.rmtree(full_path)
                    else:
                        os.remove(full_path)

        # similarly to above, tree copy may fail if we couldn't clean up properly
        # since the dest may not exist
        if not os.path.exists(dest):
            os.mkdir(dest)

        for item in os.listdir(src):
            full_sr_path = os.path.join(src, item)
            full_dest_path = os.path.join(dest, item)
            if os.path.isdir(full_sr_path):
                shutil.copytree(full_sr_path, full_dest_path)
            else:
                shutil.copy(full_sr_path, full_dest_path)

        logger.info("Restored %s to %s", src, dest)


def configure_logging(config: Config):
    level = config.logging["level"]

    base_dir = config.base_dir
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    logfile = os.path.join(base_dir, config.logging["filename"])

    logging.config.dictConfig(
        {
            "version": 1,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(levelname)s - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                }
            },
            "handlers": {
                "console": {
                    "level": level,
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                },
                "file": {
                    "level": level,
                    "class": "logging.FileHandler",
                    "formatter": "default",
                    "filename": logfile,
                },
            },
            "loggers": {"ctrl_z": {"level": level, "handlers": ["console", "file"]}},
            "disable_existing_loggers": False,
        }
    )
