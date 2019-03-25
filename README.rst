================
Snips App Helper
================

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis| |codecov| |requires|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|
.. |docs| image:: https://readthedocs.org/projects/snips-app-helpers/badge/?style=flat
    :target: https://readthedocs.org/projects/snips-app-helpers
    :alt: Documentation Status

.. |travis| image:: https://travis-ci.org/dreamermind/snips-app-helpers.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/dreamermind/snips-app-helpers

.. |requires| image:: https://requires.io/github/dreamermind/snips-app-helpers/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/dreamermind/snips-app-helpers/requirements/?branch=master

.. |codecov| image:: https://codecov.io/github/dreamermind/snips-app-helpers/coverage.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/dreamermind/snips-app-helpers

.. |version| image:: https://img.shields.io/pypi/v/snips-app-helpers.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/snips-app-helpers

.. |commits-since| image:: https://img.shields.io/github/commits-since/dreamermind/snips-app-helpers/v0.0.1.svg
    :alt: Commits since latest release
    :target: https://github.com/dreamermind/snips-app-helpers/compare/v0.0.1...master

.. |wheel| image:: https://img.shields.io/pypi/wheel/snips-app-helpers.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/snips-app-helpers

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/snips-app-helpers.svg
    :alt: Supported versions
    :target: https://pypi.org/project/snips-app-helpers

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/snips-app-helpers.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/snips-app-helpers


.. end-badges


``This is not an official Snips product !``

Handful of cli and other tools to develop with confidence Snips services.

- Adding Spec and contract between snips app and console.

.. start-badges


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

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
