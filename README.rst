=============================
collective.contact.duplicated
=============================

This add-on is part of the ``collective.contact.*`` suite. For an overview and a demo of these suite, see `collective.contact.demo <https://github.com/collective/collective.contact.demo>`__.

Add a view to manage contact duplications.

Install
=======

For the moment, this needs collective.contact.faceted with batch actions allowed.
Select two (or more) contacts (organization, held_position, person, etc) and click
on "Merge duplicated" button.

It is also possible to pass a data field with data that do not come from an existing contact. Such data may be merged with the final contact.

Tests
=====

.. image:: https://secure.travis-ci.org/collective/collective.contact.duplicated.png
    :target: http://travis-ci.org/collective/collective.contact.duplicated

.. image:: https://coveralls.io/repos/collective/collective.contact.duplicated/badge.png?branch=master
    :target: https://coveralls.io/r/collective/collective.contact.duplicated?branch=master

Extend
======

Adapters of field objects that implements IFieldRenderer interface
renders the content of a field on the compare screen.
Create a new adapter if you have specific fields.
