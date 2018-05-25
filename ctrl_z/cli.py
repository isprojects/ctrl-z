"""
Command line interface for CTRL-Z
"""
import argparse
import os
import sys

import django

from .config import DEFAULT_CONFIG_FILE


def noop():
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

    def __init__(self):
        parser = argparse.ArgumentParser(description="CTRL-Z CLI")
        parser.add_argument(
            '--config-file', help="Config file to use"
        )

        subparsers = parser.add_subparsers(help="Sub commands", dest='subcommand')

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

        self.parser = parser

    def __call__(self, config_file: str=DEFAULT_CONFIG_FILE, stdout=None):
        from . import __version__

        if stdout:
            self.stdout = stdout

        self.stdout.write(f"CTRL-Z {__version__} - Backup and recovery tool\n")

        self._setup()

        self.run(config_file)

    def _setup(self):
        self.stdout.write("Initializing...\n\n")
        self.setup()
        django.setup()

    def run(self, config_file: str):
        args = self.parser.parse_args()

        subcommand = args.subcommand
        if subcommand == 'generate_config':
            self.generate_config(args)
        elif subcommand == 'backup':
            self.backup(args, config_file)
        elif subcommand == 'restore':
            self.restore(args, config_file)

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


cli = CLI()
