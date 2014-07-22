=============================
collective.contact.duplicated
=============================

Add a view to manage contact duplications.

Install
=======

For the moment, this needs collective.contact.faceted with batch actions allowed.
Select two (or more) contacts (organization, held_position, person, etc) and click
on "Merge duplicated" button.

Tests
=====

.. image:: https://secure.travis-ci.org/tdesvenain/collective.contact.duplicated.png
    :target: http://travis-ci.org/tdesvenain/collective.contact.duplicated

.. image:: https://coveralls.io/repos/tdesvenain/collective.contact.duplicated/badge.png?branch=master
    :target: https://coveralls.io/r/tdesvenain/collective.contact.duplicated?branch=master

Extend
======

Adapters of field objects that implements IFieldRenderer interface
renders the content of a field on the compare screen.
Create a new adapter if you have specific fields.

