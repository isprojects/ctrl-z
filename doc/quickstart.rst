==========
Quickstart
==========

Installation
============

Requirements
------------

* Python 3.6 or higher
* setuptools 30.3.0 or higher
* PostgreSQL

Install
-------

.. code-block:: bash

    pip install ctrl-z

If you're using a built in backend to transfer the backups to a remote/offsite
location (currently only Google Drive is supported), you can install the
extra dependencies as well:

.. code-block:: bash

    pip install ctrl-z[transfer_backend.drive]

.. _usage:

Usage
=====

CTRL-Z exposes a CLI object to hook into your project, for example:

.. code-block:: python
    :linenos:
    :caption: backup/cli.py

    #!/usr/bin/env python
    import os
    import sys

    from ctrl_z import cli

    def setup():
        # Here you should ensure that your Django project is properly added to
        # ``sys.path``, and any other setup is done (loading ``.env`` for
        # example) so that settings can be imported in ctrl-z and django
        # initialized.
        pass


    # assign the setup function to call
    cli.setup = setup

    if __name__ == '__main__':
        # specify which config file to use
        cli(config_file='/path/to/backup/config.yml')


Once the setup around the CLI is done, you can use it.

.. _cli-help:

CLI help
--------

At any time, you can get the CLI help:

.. code-block:: bash

    python backup/cli.py --help

    CTRL-Z 0.1.2 - Backup and recovery tool
    usage: cli.py [-h] [--config-file CONFIG_FILE] [--base-dir BASE_DIR]
                  {generate_config,backup,restore} ...

    CTRL-Z CLI

    positional arguments:
      {generate_config,backup,restore}
                            Sub commands
        generate_config     Generate a config file from the default config
        backup              Create a backup
        restore             Restore a backup

    optional arguments:
      -h, --help            show this help message and exit
      --config-file CONFIG_FILE
                            Config file to use
      --base-dir BASE_DIR   Base directory override


Generate a config file
----------------------

CTRL-Z ships with a default config file that you can use as a starting point.

.. code-block:: bash

    python backup/cli.py generate_config

**Command options**:

* ``-o``, ``--output-file``: (relative or absolute) path to write the config to.
  Defaults to stdout.

See :ref:`configuration` for detailed config options documentation.


Generate a backup
-----------------

.. code-block:: bash

    python backup/cli.py backup

By default, database AND file directories (such as ``settings.MEDIA_ROOT``)
are backed up.

**Command options**:

* ``--no-db``, ``--no-database``: do not dump the databases
* ``--skip-db``: aliases (the key in ``settings.DATABASES``) to skip dumping
  for. Useful if you have a multi-db setup and only the ``default`` is important,
  for example. Use multiple times for each alias to skip.
* ``--no-files``: do not backup the (uploaded) files (e.g. ``settings.MEDIA_ROOT``)


Restore a backup
----------------

.. code-block:: bash

    python backup/cli.py backup /var/backups/2018-06-27-daily/

Restore the backup at the specified path.

**Command options**:

* ``--no-db``, ``--no-database``: do not restore the databases
* ``--skip-db``: aliases (the key in ``settings.DATABASES``) to skip restoring
  for. Useful if you have a multi-db setup and only the ``default`` is important,
  for example. Use multiple times for each alias to skip.
* ``--no-files``: do not restore the (uploaded) files (e.g. ``settings.MEDIA_ROOT``)


Transfer a backup
-----------------

.. code-block:: bash

    python backup/cli.py backup transfer

Depending on the backend used, more CLI options may be available. These show
up via the built-in :ref:`cli-help`.

The transfer is done according to the configured backend.
