.. _transfer-backends:

=================
Transfer backends
=================

Just creating backups and leaving them on the local file system is not enough.
To deal with hardware failure, you should transfer your backups to *off-site*
systems. In CTRL-Z, you can achieve this through transfer backends.

A transfer backend must:

* prepare a local backup directory, for example creating a single-file archive
  for ease of transfer.
* create the target directory hierarchy on the remote system, if needed
* be able to say if a local backup already exists on the remote or not
* be able to upload the prepared backup to the remote (and verify it's integrity)

A transfer backend may optionally define subcommands for the main command line
interface.

Available backends:

* :ref:`transfer-backend-drive`

Third party backends can be developed if needed, and installed as a separate
package. The YAML configuration is used to specify which backend to use and
which ``__init__`` parameters are required for the backend to configure
runtime options.

Base backend
============

Custom backends should inherit from the base backend to guarantee API
compatibility.

This backend is not functional by itself - it's an abstract base class.

.. autoclass:: ctrl_z.transfer.backends.base.Base
   :members:


.. _transfer-backend-drive:

Google Drive
============

The Google Drive backend uploads the documents to Google Drive through the
Drive API. You need to create a `service account <google service accounts>`_
(see :ref:`drive-getting-started`) to be able to run the transfer without
interaction.

.. todo:: See how to integrate with `team drives`_.

The Drive backend:

* creates the subfolders in Drive to store the backups if needed
* creates a gzipped tar-archive of the backup on the local file system
* checks if the backup exists by matching the name of the archive and the md5
  checksum against the (potentially) existing file on Drive
* uploads the archive to Drive and verifies integrity by comparing the
  reported checksum with the local checksum

Additionally, this backend provides some :ref:`drive-cli-extensions`.

.. _drive-getting-started:

Getting started
---------------

`google service accounts`_ are Google's way to interact with APIs on behalf
of a single user/entity. This is in contrast with OAUTH2 based flows where the
application using the Drive API typically interacts with the *account of the
end user*. For transfer backends, there are no end-users.

One drawback is that you cannot have the Google Drive interface as the service
account, there is only API access. You can work around this by sharing the
folder holding the backups in Drive with yourself, see the
:ref:`drive-cli-extensions`.

#. In the `google cloud console`_, create or select the project to use for the
   backup transfer.
#. Next, click **+ Create service account**, and fill out the fields, e.g.:

   * Service account name: isp-backups
   * Project role: you don't need to specify any role
   * Check 'Furnish a private key' and check the default 'JSON'

#. Backup the key file download to your browser - there's no way to obtain this
   again. You can generate new keys of course.

#. Configure CTRL-Z - in your ``config.yml``, ensure you have:

    .. code-block:: yaml

        transfer_backend: ctrl_z.transfer.backends.google_drive.Backend
        transfer_backend_init_kwargs:
            client_secrets: /path/to/the/downloaded/key/file.json
        transfer_path: /some/root/dir


    It's recommended to create at least one root directory to facilitate
    sharing the folder with other people, since it's not possible to share the
    root folder of Drive.

#. Test the connection:

    .. code-block:: bash

        $ python cli.py transfer test_connection


.. _drive-cli-extensions:

CLI extensions
--------------

The Drive backend extends the CLI with some subcommands.

Connection test
+++++++++++++++

To verify that your credentials are correct, you can do a connection test:

.. code-block:: bash

    $ python cli.py transfer test_connection

Show quota
++++++++++

You can display the quota usage without needing to initiate a transfer:

.. code-block:: bash

    $ python cli.py transfer show_quota

Give read access
++++++++++++++++

You can share the root foldder with:

.. code-block:: bash

    $ python cli.py transfer give_permissions hello@example.com

The owner of the e-mail address then has read access to the folder in their
Drive via the 'Shared with me' tab.


.. _google service accounts: https://cloud.google.com/iam/docs/service-accounts
.. _google cloud console: https://console.cloud.google.com
.. _team drives: https://stackoverflow.com/questions/43243865/how-to-access-team-drive-using-service-account-with-google-drive-net-api-v3
