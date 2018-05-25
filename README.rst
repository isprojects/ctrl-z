==========================================
CTRL-Z - A Django backup and recovery tool
==========================================

CTRL-Z (control-zee) is a backup and recovery tool for Django projects.

Its goals is to be operating system agnostic in creating and restoring backups,
while being flexible through a yaml configuration file.

.. note:: Warning: currently only PostgreSQL is supported

.. note:: This package is currently closed source

.. contents::

.. section-numbering::

Features
========

* Supports Linux, Windows, MacOS
* Django project inspection:

    * backs up configured databases using ``settings.DATABASES``
    * backs up file directories such as ``settings.MEDIA_ROOT``

* YAML-based, minimal configuration
* Simple Python/CLI APIs for backup creation and restoration

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


Usage
=====

.. note:: TODO: finish readme, write docs etc.
