.. _configuration:

=============
Configuration
=============

Configuration is done in YAML format. You can pass the config file to use
to the ``cli`` object (see :ref:`usage`).

Global config options
=====================

``base_dir``
------------

Type: string indicating filesystem path.

The base directory where backups are saved to. This should be an on-disk
location, defaults to ``/var/backups/``.

Within this directory, date-stamped backup directories will be created.

Old backups in this directory are rotated according to the :ref:`retention policy`.

.. note:: As end user, you are responsible of setting up a mechanism to
   transfer backups to off-site storage.


``logging``
-----------

Type: object.

CTRL-Z uses stdlib logging to log all its actions. If e-mail notifications are
set up, the contents of the log are mailed to indicated receivers.

``logging.filename``
    name of the log file, will be created inside the date-stamped backup
    directory.

``logging.level``
    Log level to control log verbosity. Defaults to INFO. Uses the available
    stdlib log levels.

.. _retention policy:

``retention_policy``
--------------------

Type: object

CTRL-Z rotates your backups for you to prevent you from running out of disk
space on (production) machines.

``retention_policy.day_of_week``
    Integer, 0-6, indicating which day counts as weekly backup. Defaults to
    0, which is Monday.

``retention_policy.days_to_keep``
   Number of daily backups to keep, including the backup-to-be-created.
   Defaults to 7.

``retention_policy.weeks_to_keep``
   Same as ``days_to_keep``, except in weeks.


``report``
----------

Type: object

CTRL-Z can use Django's e-mail machinery to send an e-mail report. Useful to
have confirmation that the backup did indeed run/complete without issues.

``report.enabled``
    Boolean, whether to send reports or not. Defaults to True.

``report.to``
    List of e-mail address to send the report to. Defaults to
    ``root@localhost``


``database``
------------

Which databases need to be dumped/restored are introspected from
``settings.DATABASES``. Database configuration here is related to CTRL-Z
internals.

``database.test_function``
    String, python path.
    After restoring, CTRL-Z tests if the DB restore was not a failure. By
    default, the check tests if the ``django_migrations`` table is not empty.
    This is not water-tight, and you can provide your own function as long
    as it can be imported.

    The function signature is:

    .. code-block:: python

        def my_restore_test(using: str='default') -> bool:
            """
            :param using: the alias of the database to check.
            """
            pass


``files``
---------

Control how CTRL-Z runs backups of your (uploaded) files.

``files.overwrite_existing_directory``
    Boolean, defaults to True. If the folder already exists in the backup
    location, replace it. Useful when running the backup multiple times a day.

``files.directories``
    List of setting names to include in the backup. Defaults to
    ``['MEDIA_ROOT']``, which means that only ``settings.MEDIA_ROOT`` will be
    included.


``pg_dump_binary``
------------------

Which binary to use to dump the database. Defaults to ``/usr/bin/pg_dump``.

``pg_restore_binary``
---------------------

Which binary to use to dump the database. Defaults to ``/usr/bin/pg_restore``.
