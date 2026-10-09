# -*- coding: utf-8 -*-
"""Tests of fields.py: the IFieldDiff adapters of the fields of the contact types."""

from collections import namedtuple
from collective.contact.core.behaviors import IBirthday
from collective.contact.core.behaviors import IContactDetails
from collective.contact.duplicated.fields import BooleanFieldDiff
from collective.contact.duplicated.fields import ChoiceFieldDiff
from collective.contact.duplicated.fields import CollectionFieldDiff
from collective.contact.duplicated.fields import ContactChoiceFieldDiff
from collective.contact.duplicated.fields import DateFieldDiff
from collective.contact.duplicated.fields import DictRowFieldDiff
from collective.contact.duplicated.fields import FieldDiff
from collective.contact.duplicated.fields import FileFieldDiff
from collective.contact.duplicated.fields import ImageFieldDiff
from collective.contact.duplicated.fields import RelationFieldDiff
from collective.contact.duplicated.fields import RichTextFieldDiff
from collective.contact.duplicated.interfaces import IFieldDiff
from collective.contact.duplicated.testing import IntegrationTestCase
from plone import api
from plone.app.relationfield.behavior import IRelatedItems
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.textfield.value import RichTextValue
from plone.dexterity.interfaces import IDexterityFTI
from plone.namedfile.file import NamedBlobFile
from plone.namedfile.file import NamedBlobImage
from Products.CMFPlone.utils import safe_unicode
from z3c.relationfield.relation import RelationValue
from zope.component import getUtility
from zope.intid.interfaces import IIntIds

import base64
import datetime
import unittest


# 1x1 PNG
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC")


def schema_field(portal_type, name):
    return getUtility(IDexterityFTI, name=portal_type).lookupSchema()[name]


class FieldDiffTestCase(IntegrationTestCase):

    def setUp(self):
        super(FieldDiffTestCase, self).setUp()
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        login(self.portal, TEST_USER_NAME)
        self.directory = self.portal.mydirectory
        self.degaulle = self.directory.degaulle
        self.pepper = self.directory.pepper
        self.armeedeterre = self.directory.armeedeterre

    def relation(self, obj):
        return RelationValue(getUtility(IIntIds).getId(obj))


class TestBaseFieldDiff(FieldDiffTestCase):
    """BaseFieldDiff methods, through FieldDiff (zope.schema IField adapter)"""

    def setUp(self):
        super(TestBaseFieldDiff, self).setUp()
        self.diff = IFieldDiff(schema_field("person", "lastname"))

    def test___init__(self):
        self.assertIsInstance(self.diff, FieldDiff)
        self.assertEqual(self.diff.name, "lastname")
        self.assertIs(self.diff.field, schema_field("person", "lastname"))

    def test___repr__(self):
        self.assertEqual(repr(self.diff), "<FieldDiff - lastname>")

    def test_get_value(self):
        self.assertEqual(self.diff.get_value(self.degaulle), "De Gaulle")
        # a content without this field
        self.assertIsNone(self.diff.get_value(self.armeedeterre))

    def test_render(self):
        self.assertEqual(self.diff.render(self.degaulle), "De Gaulle")
        self.assertIsNone(self.diff.render(self.armeedeterre))
        self.degaulle.lastname = ""
        self.assertIsNone(self.diff.render(self.degaulle))

    def test_render_collection_entry(self):
        self.assertEqual(self.diff.render_collection_entry(self.degaulle, "De Gaulle"), "De Gaulle")
        self.assertEqual(self.diff.render_collection_entry(self.degaulle, None), "")

    def test_is_different(self):
        self.assertTrue(self.diff.is_different("De Gaulle", "Pepper"))
        self.assertFalse(self.diff.is_different("Pepper", "Pepper"))
        self.assertTrue(self.diff.is_different(None, "Pepper"))

    def test_copy(self):
        # from a content
        self.diff.copy(self.pepper, self.degaulle)
        self.assertEqual(self.degaulle.lastname, "Pepper")
        # from the extra data (dict)
        self.diff.copy({"lastname": "Le Général"}, self.degaulle)
        self.assertEqual(self.degaulle.lastname, "Le Général")
        # from an acquisition property of a held position: the person value
        IFieldDiff(schema_field("person", "person_title")).copy(self.degaulle.adt, self.pepper)
        self.assertEqual(self.pepper.person_title, "Général")


class TestFileFieldDiff(FieldDiffTestCase):

    def test_render(self):
        diff = IFieldDiff(schema_field("letter", "file"))
        self.assertIsInstance(diff, FileFieldDiff)
        letter = api.content.create(container=self.portal, type="letter", id="letter")
        self.assertEqual(diff.render(letter), "")
        letter.file = NamedBlobFile(data=b"%PDF-1.4", filename="letter.pdf")
        self.assertEqual(diff.render(letter), "letter.pdf")


class TestImageFieldDiff(FieldDiffTestCase):

    def test_render(self):
        diff = IFieldDiff(schema_field("person", "photo"))
        self.assertIsInstance(diff, ImageFieldDiff)
        self.assertEqual(diff.render(self.degaulle), "")
        self.degaulle.photo = NamedBlobImage(data=PNG, filename="degaulle.png")
        render = diff.render(self.degaulle)
        self.assertTrue(render.startswith('<img src="http://nohost/plone/mydirectory/degaulle/@@images/'), render)
        self.assertIn('title="degaulle.png" alt="degaulle.png"', render)


class TestBooleanFieldDiff(FieldDiffTestCase):

    def test_render(self):
        diff = IFieldDiff(IContactDetails["use_parent_address"])
        self.assertIsInstance(diff, BooleanFieldDiff)
        self.assertEqual(diff.render(self.directory.rambo), "Yes")
        self.assertEqual(diff.render(self.degaulle), "No")
        # field not set
        self.assertEqual(diff.render(self.portal.folder), "")


class TestDateFieldDiff(FieldDiffTestCase):

    def setUp(self):
        super(TestDateFieldDiff, self).setUp()
        self.diff = IFieldDiff(IBirthday["birthday"])

    def test_render(self):
        self.assertIsInstance(self.diff, DateFieldDiff)
        # localized date: the format depends on the Plone version
        render = self.diff.render(self.degaulle)
        self.assertIn("1901", render)
        self.assertIn("22", render)
        self.assertEqual(self.diff.render(self.directory.rambo), "")

    def test_render_collection_entry(self):
        self.assertEqual(self.diff.render_collection_entry(self.degaulle, datetime.date(1901, 11, 22)), "1901/11/22")


class TestChoiceFieldDiff(FieldDiffTestCase):

    def setUp(self):
        super(TestChoiceFieldDiff, self).setUp()
        # vocabulary of the field
        self.gender = IFieldDiff(schema_field("person", "gender"))
        # named vocabulary
        self.organization_type = IFieldDiff(schema_field("organization", "organization_type"))

    def test__get_vocabulary_value(self):
        self.assertIsInstance(self.gender, ChoiceFieldDiff)
        self.assertIsInstance(self.organization_type, ChoiceFieldDiff)
        self.assertEqual(self.gender._get_vocabulary_value(self.degaulle, "F"), "Female")
        self.assertEqual(self.organization_type._get_vocabulary_value(self.armeedeterre, "army"), "Army")
        # unknown token, empty value
        self.assertEqual(self.gender._get_vocabulary_value(self.degaulle, "X"), "X")
        self.assertIsNone(self.gender._get_vocabulary_value(self.degaulle, None))
        # extra data (temporary object of the compare view): the raw value
        extra = namedtuple("mystruct", ["gender"])(gender="M")
        self.assertEqual(self.gender._get_vocabulary_value(extra, "M"), "M")

    def test_render(self):
        self.assertEqual(self.gender.render(self.degaulle), "Male")
        self.assertEqual(self.organization_type.render(self.armeedeterre), "Army")
        self.assertIsNone(self.gender.render(self.directory.rambo))

    def test_render_collection_entry(self):
        self.assertEqual(self.gender.render_collection_entry(self.degaulle, "M"), "Male")
        self.assertEqual(self.gender.render_collection_entry(self.degaulle, None), "")


class TestCollectionFieldDiff(FieldDiffTestCase):

    def setUp(self):
        super(TestCollectionFieldDiff, self).setUp()
        self.diff = IFieldDiff(IRelatedItems["relatedItems"])
        self.letter = api.content.create(container=self.portal, type="letter", id="letter")

    def test_is_different(self):
        self.assertIsInstance(self.diff, CollectionFieldDiff)
        # None, [] and () are the same
        self.assertFalse(self.diff.is_different(None, []))
        self.assertFalse(self.diff.is_different((), None))
        self.assertFalse(self.diff.is_different(["a"], ["a"]))
        self.assertTrue(self.diff.is_different(["a"], ["b"]))
        self.assertTrue(self.diff.is_different([], ["b"]))

    def test_render(self):
        self.letter.relatedItems = []
        self.assertIsNone(self.diff.render(self.letter))
        self.letter.relatedItems = None
        self.assertEqual(self.diff.render(self.letter), "")
        # entries rendered by the value type adapter, joined by commas
        # (Plone 4: UnicodeDecodeError with a non ascii title, see MIGRATION.md)
        self.letter.relatedItems = [self.relation(self.pepper), self.relation(self.directory.rambo)]
        self.assertEqual(
            safe_unicode(self.diff.render(self.letter)),
            '<a href="http://nohost/plone/mydirectory/pepper" target="new">Mister Pepper</a>, '
            '<a href="http://nohost/plone/mydirectory/rambo" target="new">John Rambo</a>',
        )


class TestRichTextFieldDiff(FieldDiffTestCase):

    def setUp(self):
        super(TestRichTextFieldDiff, self).setUp()
        self.diff = IFieldDiff(schema_field("organization", "activity"))

    def test_render(self):
        self.assertIsInstance(self.diff, RichTextFieldDiff)
        self.assertEqual(self.diff.render(self.armeedeterre), "")
        # long text: truncated to 50 characters
        self.armeedeterre.activity = RichTextValue(
            "The French Army is the land-based component of the French Armed Forces", "text/plain", "text/plain"
        )
        render = self.diff.render(self.armeedeterre)
        self.assertEqual(len(render), 50)
        self.assertTrue(render.endswith("..."))
        self.assertIn("The French Army", render)

    @unittest.expectedFailure
    def test_render_short_text(self):
        """Plone 4 bug: a text of 50 characters or less renders None (nothing is returned)"""
        self.armeedeterre.activity = RichTextValue("Land forces", "text/plain", "text/plain")
        self.assertIn("Land forces", self.diff.render(self.armeedeterre))


class TestRelationFieldDiff(FieldDiffTestCase):

    def setUp(self):
        super(TestRelationFieldDiff, self).setUp()
        # value type of the related items field: RelationChoice
        self.diff = IFieldDiff(IRelatedItems["relatedItems"].value_type)

    def test_is_different(self):
        self.assertIsInstance(self.diff, RelationFieldDiff)
        self.assertFalse(self.diff.is_different(None, None))
        # a value against no value is not a difference
        self.assertFalse(self.diff.is_different(None, self.relation(self.pepper)))
        self.assertFalse(self.diff.is_different(self.relation(self.pepper), None))
        self.assertFalse(self.diff.is_different(self.relation(self.pepper), self.relation(self.pepper)))
        self.assertTrue(self.diff.is_different(self.relation(self.degaulle), self.relation(self.pepper)))

    def test_render(self):
        # a named relation field: position of the held positions
        diff = RelationFieldDiff(schema_field("held_position", "position"))
        self.assertEqual(diff.render(self.portal.folder), "")
        # Title() is utf-8 bytes on Plone 4
        self.assertEqual(
            safe_unicode(diff.render(self.degaulle.adt)),
            '<a href="http://nohost/plone/mydirectory/armeedeterre" target="new">Armée de terre</a>',
        )

    def test_render_collection_entry(self):
        self.assertEqual(self.diff.render_collection_entry(self.degaulle, None), "")
        self.assertEqual(
            safe_unicode(self.diff.render_collection_entry(self.degaulle, self.relation(self.pepper))),
            '<a href="http://nohost/plone/mydirectory/pepper" target="new">Mister Pepper</a>',
        )


class TestDictRowFieldDiff(FieldDiffTestCase):
    """position_types of the directory: a list of dict rows (datagridfield)"""

    def setUp(self):
        super(TestDictRowFieldDiff, self).setUp()
        field = schema_field("directory", "position_types")
        self.assertIsInstance(IFieldDiff(field), CollectionFieldDiff)
        self.diff = IFieldDiff(field.value_type)
        self.assertIsInstance(self.diff, DictRowFieldDiff)

    @unittest.expectedFailure
    def test_render(self):
        """Plone 4 bug: AttributeError, the sub field adapters have no render_header method"""
        self.assertEqual(
            IFieldDiff(schema_field("directory", "position_types")).render(self.directory)[:24],
            "Name : General / Token :",
        )

    @unittest.expectedFailure
    def test_render_collection_entry(self):
        """Plone 4 bug: AttributeError, the sub field adapters have no render_header method"""
        self.assertEqual(
            self.diff.render_collection_entry(self.directory, {"name": "General", "token": "general"}),
            "Name : General / Token : general",
        )


class TestContactChoiceFieldDiff(FieldDiffTestCase):

    def test_render_collection_entry(self):
        diff = IFieldDiff(schema_field("held_position", "position"))
        self.assertIsInstance(diff, ContactChoiceFieldDiff)
        self.assertEqual(diff.render_collection_entry(self.degaulle.adt, None), "")
        # full title of the organization
        self.assertEqual(
            diff.render_collection_entry(self.degaulle.adt, self.directory.pepper.sergent_pepper.position),
            '<a href="http://nohost/plone/mydirectory/armeedeterre/corpsa/divisionalpha/regimenth/brigadelh/'
            'sergent_lh" target="new">Sergent de la brigade LH (Armée de terre / Corps A / Division Alpha / '
            "Régiment H / Brigade LH)</a>",
        )
        # through render
        self.assertEqual(
            diff.render(self.degaulle.adt),
            '<a href="http://nohost/plone/mydirectory/armeedeterre" target="new">Armée de terre</a>',
        )
