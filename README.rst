=============================
collective.contact.duplicated
=============================

Add a view to manage contact duplications.

Install
=======

For the moment, this needs collective.contact.faceted with batch actions allowed.
Select two (or more) contacts (organization, held_position, person, etc) and click
on "Merge duplicated" button.

Extend
======

Adapters of field objects that implements IFieldRenderer interface
renders the content of a field on the compare screen.
Create a new adapter if you have specific fields.

