=========
Vellumbot
=========

.. sidebar:: Download

    Download the `latest source`_ or `browse the source`_.

.. _latest source: http://vellumbot-source.goonmill.org/archive/tip.tar.gz

.. _browse the source: http://vellumbot-source.goonmill.org/file/tip/

.. image:: /static/vellumbotlogo.png

Vellumbot is a D&D-oriented IRC bot.  It rolls dice and can remember user
macros so players don't have to remember their own dice rolls.

README
------

Installation: Ubuntu Users
~~~~~~~~~~~~~~~~~~~~~~~~~~

..

Installation
~~~~~~~~~~~~

..


I. easy_install or pip method
=============================
With setuptools (Ubuntu: sudo apt-get install python-setuptools), you can
install Vellumbot without even downloading it first, by using
::

    sudo easy_install vellumbot

If you have pip_, you should use that
::

    sudo pip install vellumbot

.. _pip: http://pip.openplans.org/


II. source method
=================
::

    python setup.py build; sudo python setup.py install

Optionally, run::

    make tests

in the source directory to see the unit tests run.
 

Quick Start 
~~~~~~~~~~~




Contributing and Reporting Bugs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Vellumbot has a `bug tracker <https://bugs.launchpad.net/vellumbot>`_ on Launchpad.

For more information on contributing, including the URL of the source
repository for Hypy, go to `DevelopmentCentral
<http://wiki.goonmill.org/DevelopmentCentral>`_ on the wiki_.

.. _wiki: http://wiki.goonmill.org/

It bears emphasizing that **bugs with reproducible steps, patches and unit
tests** (in that order) **get fixed sooner**.

License
~~~~~~~
MIT License

Vellumbot (c) Cory Dodt, 2008.
