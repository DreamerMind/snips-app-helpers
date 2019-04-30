=================
Snips App Helpers
=================

.. image:: https://readthedocs.org/projects/snips-app-helpers/badge/?style=flat
    :target: https://readthedocs.org/projects/snips-app-helpers
    :alt: Documentation Status

.. image:: https://travis-ci.org/DreamerMind/snips-app-helpers.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/DreamerMind/snips-app-helpers


.. image:: https://codecov.io/github/dreamermind/snips-app-helpers/coverage.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/dreamermind/snips-app-helpers

.. image:: https://img.shields.io/pypi/v/snips-app-helpers.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/snips-app-helpers

.. image:: https://img.shields.io/pypi/pyversions/snips-app-helpers.svg
    :alt: Supported versions
    :target: https://pypi.org/project/snips-app-helpers

.. image:: https://img.shields.io/github/license/dreamermind/snips-app-helpers.svg
   :target: https://github.com/dreamermind/snips-app-helpers/blob/master/LICENSE
   :alt: License


``WARNING ! can be used by internal snipsters only for now :( due to dataset.json shipping limitation``

``This is not an official Snips product !``

Snips App Helpers help you to declare, test, and check your snips application.
Here is the list of tools availlable:

- Adding contract Spec between Snips Action and Console Assistant and a cli tool to generate compliance report.

- MiddleWare Action that remap any Action intent & slots to another Action based on the given spec

Installation
============

::

    pip install snips-app-helpers

Documentation
=============

https://snips-app-helpers.readthedocs.io/


Development
===========


To run the all tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

Tested only on unix like systems
::

   PYTEST_ADDOPTS=--cov-append tox
