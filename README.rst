.. You should enable this project on travis-ci.org and coveralls.io to make
   these badges work. The necessary Travis and Coverage config files have been
   generated for you.

.. image:: https://travis-ci.org/vrk-kpa/ckanext-matomo.svg?branch=master
    :target: https://travis-ci.org/vrk-kpa/ckanext-matomo

.. image:: https://coveralls.io/repos/vrk-kpa/ckanext-matomo/badge.svg
  :target: https://coveralls.io/r/vrk-kpa/ckanext-matomo

.. image:: https://pypip.in/download/ckanext-matomo/badge.svg
    :target: https://pypi.python.org/pypi//ckanext-matomo/
    :alt: Downloads

.. image:: https://pypip.in/version/ckanext-matomo/badge.svg
    :target: https://pypi.python.org/pypi/ckanext-matomo/
    :alt: Latest Version

.. image:: https://pypip.in/py_versions/ckanext-matomo/badge.svg
    :target: https://pypi.python.org/pypi/ckanext-matomo/
    :alt: Supported Python versions

.. image:: https://pypip.in/status/ckanext-matomo/badge.svg
    :target: https://pypi.python.org/pypi/ckanext-matomo/
    :alt: Development Status

.. image:: https://pypip.in/license/ckanext-matomo/badge.svg
    :target: https://pypi.python.org/pypi/ckanext-matomo/
    :alt: License

=============
ckanext-matomo
=============

.. Put a description of your extension here:
   What does it do? What features does it have?
   Consider including some screenshots or embedding a video!


------------
Requirements
------------

For example, you might want to mention here which versions of CKAN this
extension works with.


------------
Installation
------------

.. Add any additional install steps to the list below.
   For example installing any non-Python dependencies or adding any required
   config settings.

To install ckanext-matomo:

1. Activate your CKAN virtual environment, for example::

     . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-matomo Python package into your virtual environment::

     pip install ckanext-matomo

3. Add ``matomo`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``).

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu::

     sudo service apache2 reload


---------------
Config Settings
---------------


    # The domain used for matomo analytics
    ckanext.matomo.domain = http://example.com/

    # The site id used in matomo
    ckanext.matomo.site_id = 1

    # The domain where matomo script is downloaded
    # (optional, default ckanext.matomo.domain)
    ckanext.matomo.script_domain

------------------------
Development Installation
------------------------

To install ckanext-matomo for development, activate your CKAN virtualenv and
do::

    git clone https://github.com/vrk-kpa/ckanext-matomo.git
    cd ckanext-matomo
    python setup.py develop
    pip install -r dev-requirements.txt


-----------------
Running the Tests
-----------------

To run the tests, do::

    nosetests --nologcapture --with-pylons=test.ini

To run the tests and produce a coverage report, first make sure you have
coverage installed in your virtualenv (``pip install coverage``) then run::

    nosetests --nologcapture --with-pylons=test.ini --with-coverage --cover-package=ckanext.matomo --cover-inclusive --cover-erase --cover-tests


---------------------------------
Registering ckanext-matomo on PyPI
---------------------------------

ckanext-matomo should be availabe on PyPI as
https://pypi.python.org/pypi/ckanext-matomo. If that link doesn't work, then
you can register the project on PyPI for the first time by following these
steps:

1. Create a source distribution of the project::

     python setup.py sdist

2. Register the project::

     python setup.py register

3. Upload the source distribution to PyPI::

     python setup.py sdist upload

4. Tag the first release of the project on GitHub with the version number from
   the ``setup.py`` file. For example if the version number in ``setup.py`` is
   0.0.1 then do::

       git tag 0.0.1
       git push --tags


----------------------------------------
Releasing a New Version of ckanext-matomo
----------------------------------------

ckanext-matomo is availabe on PyPI as https://pypi.python.org/pypi/ckanext-matomo.
To publish a new version to PyPI follow these steps:

1. Update the version number in the ``setup.py`` file.
   See `PEP 440 <http://legacy.python.org/dev/peps/pep-0440/#public-version-identifiers>`_
   for how to choose version numbers.

2. Create a source distribution of the new version::

     python setup.py sdist

3. Upload the source distribution to PyPI::

     python setup.py sdist upload

4. Tag the new release of the project on GitHub with the version number from
   the ``setup.py`` file. For example if the version number in ``setup.py`` is
   0.0.2 then do::

       git tag 0.0.2
       git push --tags
