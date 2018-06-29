==========================================
CTRL-Z - A Django backup and recovery tool
==========================================

CTRL-Z (control-zee) is a backup and recovery tool for Django projects.

Its goals are to be operating system agnostic in creating and restoring backups,
while being flexible through a yaml configuration file.

|build-status| |requirements| |coverage| |docs|

|python-versions| |django-versions| |pypi-version|

.. note:: Warning: currently only PostgreSQL is supported

.. contents::

.. section-numbering::

Features
========

* Supports Linux, Windows, MacOS
* Django project inspection:

    * backs up configured databases using ``settings.DATABASES``
    * backs up file directories such as ``settings.MEDIA_ROOT`` (configurable)

* stdlib ``logging`` based reporting + e-mailing of backup/restore report
* YAML-based, minimal configuration
* Simple Python/CLI APIs for backup creation and restoration

Installation and usage
======================

See the `documentation`_.


.. |build-status| image:: https://travis-ci.org/isprojects/ctrl-z.svg?branch=develop
    :target: https://travis-ci.org/isprojects/ctrl-z
    :alt: Build status

.. |requirements| image:: https://requires.io/github/isprojects/ctrl-z/requirements.svg?branch=develop
    :target: https://requires.io/github/isprojects/ctrl-z/requirements/?branch=develop
    :alt: Requirements status

.. |coverage| image:: https://codecov.io/gh/isprojects/ctrl-z/branch/develop/graph/badge.svg
    :target: https://codecov.io/gh/isprojects/ctrl-z
    :alt: Coverage status

.. |python-versions| image:: https://img.shields.io/pypi/pyversions/ctrl-z.svg

.. |django-versions| image:: https://img.shields.io/pypi/djversions/ctrl-z.svg

.. |pypi-version| image:: https://img.shields.io/pypi/v/ctrl-z.svg
    :target: https://pypi.org/project/ctrl-z/

.. |docs| image:: https://readthedocs.org/projects/ctrl-z/badge/?version=latest
    :target: https://ctrl-z.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. _documentation: https://ctrl-z.readthedocs.io/en/latest/
