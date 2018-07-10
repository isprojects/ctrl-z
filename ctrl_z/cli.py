"""
Command line interface for CTRL-Z
"""
import argparse
import logging
import os
import sys

import django

from .backup import Backup, configure_logging
from .config import DEFAULT_CONFIG_FILE
from .transfer import BackupTransfer

logger = logging.getLogger(__name__)


def noop(*args, **kwargs):
    pass


class readable_dir(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir = values
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentTypeError(
                "{0} is not a valid path".format(prospective_dir)
            )
        if os.access(prospective_dir, os.R_OK):
            setattr(namespace, self.dest, prospective_dir)
        else:
            raise argparse.ArgumentTypeError(
                "{0} is not a readable dir".format(prospective_dir)
            )


class CLI:
    """
    Core CLI implementation.

    Requires the developer to set up the python path correctly so that django
    can initialize properly.

    Example usage::

        >>> from ctrl_z import cli
        >>> def setup():
        ...     sys.path.insert(1, '/path/to/my/project/root/')
        ...     from myproject.setup import setup_env
        ...     setup_env()
        ...
        >>> cli.setup = setup
        >>> if __name__ == '__main__':
        ...     cli(config_file='/path/to/backup/config.yml')

    """

    setup = noop
    stdout = sys.stdout
    stderr = sys.stderr
    _backup = None

    def __init__(self):
        parser = argparse.ArgumentParser(description="CTRL-Z CLI")
        parser.add_argument('--config-file', help="Config file to use")
        parser.add_argument('--base-dir', help="Base directory override")

        subparsers = parser.add_subparsers(
            help="Sub commands", dest='subcommand'
        )

        # config file generation
        parser_gen_config = subparsers.add_parser(
            'generate_config',
            help="Generate a config file from the default config"
        )
        parser_gen_config.add_argument(
            '-o', '--output-file', help="Output file to write the config to"
        )

        # backup creation
        parser_backup = subparsers.add_parser('backup', help="Create a backup")
        parser_backup.add_argument(
            '--no-db', '--no-database', dest='backup_db',
            action='store_false', default=True,
            help="Do not backup the databases"
        )
        parser_backup.add_argument(
            '--skip-db', nargs='+',
            help='Database aliases to skip - use multiple times for each '
                 'alias to skip'
        )
        parser_backup.add_argument(
            '--no-files', dest='backup_files', action='store_false',
            default=True, help="Do not backup files"
        )

        # backup restoration
        parser_restore = subparsers.add_parser(
            'restore', help="Restore a backup"
        )
        parser_restore.add_argument(
            'backup_dir', action=readable_dir,
            help="Directory containing the backups"
        )
        parser_restore.add_argument(
            '--no-db', '--no-database', dest='restore_db',
            action='store_false', default=True,
            help="Do not restore the databases"
        )
        parser_restore.add_argument(
            '--skip-db', nargs='+',
            help='Database aliases to skip - use multiple times for each '
                 'alias to skip'
        )
        parser_restore.add_argument(
            '--no-files', dest='restore_files', action='store_false',
            default=True, help="Do not restore files"
        )

        # backup transfer
        parser_transfer = subparsers.add_parser(
            'transfer', help='Transfer the backups to an off-site location'
        )

        self.parser = parser

    def __call__(self, args=None, config_file: str=DEFAULT_CONFIG_FILE, stdout=None, stderr=None):
        from . import __version__

        if stdout:
            self.stdout = stdout

        if stderr:
            self.stderr = stderr

        self.stderr.write(f"CTRL-Z {__version__} - Backup and recovery tool\n")

        args = self.parser.parse_args(args or sys.argv[1:])
        config_file = args.config_file or config_file

        self._setup()

        self.run(args, config_file)

    def _setup(self):
        self.stderr.write("Initializing...\n\n")
        self.setup()
        django.setup()

    def run(self, options, config_file: str):
        subcommand = options.subcommand
        conf_overrides = {}
        if options.base_dir:
            conf_overrides['base_dir'] = options.base_dir

        if subcommand == 'restore':
            self._backup = Backup.prepare_restore(
                config_file, options.backup_dir
            )
        else:
            self._backup = Backup.from_config(
                config_file,
                **conf_overrides
            )

        configure_logging(self._backup.config)

        if subcommand == 'generate_config':
            self.generate_config(options)
        elif subcommand == 'backup':
            self.backup(options)
        elif subcommand == 'restore':
            self.restore(options)
        elif subcommand == 'transfer':
            self.transfer(options, config_file, conf_overrides)
        else:
            self.parser.print_help()

    def generate_config(self, options):
        """
        Read the default config and write it to stdout or the requested
        output file.
        """
        with open(DEFAULT_CONFIG_FILE, 'r') as _default_config:
            config = _default_config.read()

        if options.output_file:
            with open(options.output_file, 'w') as outfile:
                outfile.write(config)
        else:
            self.stdout.write(config)

    def backup(self, options):
        backup_db = options.backup_db
        skip_db = options.skip_db
        backup_files = options.backup_files

        backup = self._backup

        # perform the backup
        has_errors = False
        try:
            backup.full(db=backup_db, skip_db=skip_db, files=backup_files)
        except Exception:
            has_errors = True
            logger.exception("Backup failed")
            raise
        finally:
            backup.report(has_errors)

    def restore(self, options):
        restore_db = options.restore_db
        skip_db = options.skip_db
        restore_files = options.restore_files

        backup = self._backup

        # perform the restore
        has_errors = False
        try:
            backup.restore(db=restore_db, skip_db=skip_db, files=restore_files)
        except Exception:
            has_errors = True
            logger.exception("Restore failed")
            raise
        finally:
            backup.report(has_errors)

    def transfer(self, options, config_file, conf_overrides):
        conf_overrides['use_parent_dir'] = True

        transfer = BackupTransfer.from_config(config_file, **conf_overrides)
        transfer.show_info()
        transfer.sync_to_remote()


cli = CLI()
