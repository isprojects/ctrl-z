.. CTRL-Z documentation master file, created by
   sphinx-quickstart on Tue Jun 27 15:38:51 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to CTRL-Z's documentation!
===========================================

|build-status| |coverage|

|python-versions| |django-versions| |pypi-version|

CTRL-Z (control-zee) is a backup and recovery tool for Django projects.

Its goals are to be operating system agnostic in creating and restoring backups,
while being flexible through a yaml configuration file.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quickstart
   configuration


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. |build-status| image:: https://travis-ci.org/isprojects/ctrl-z.svg?branch=develop
    :target: https://travis-ci.org/isprojects/ctrl-z

.. |coverage| image:: https://codecov.io/gh/isprojects/ctrl-z/branch/develop/graph/badge.svg
    :target: https://codecov.io/gh/isprojects/ctrl-z
    :alt: Coverage status

.. |python-versions| image:: https://img.shields.io/pypi/pyversions/ctrl-z.svg

.. |django-versions| image:: https://img.shields.io/pypi/djversions/ctrl-z.svg

.. |pypi-version| image:: https://img.shields.io/pypi/v/ctrl-z.svg
    :target: https://pypi.org/project/ctrl-z/

.. _sendfile: https://pypi.org/project/django-sendfile2/

