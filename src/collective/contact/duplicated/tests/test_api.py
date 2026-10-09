# -*- coding: utf-8 -*-
"""Tests of api.py."""

from collective.contact.core.behaviors import IContactDetails
from collective.contact.duplicated.api import get_back_references
from collective.contact.duplicated.api import get_fields
from collective.contact.duplicated.api import get_fieldsets
from collective.contact.duplicated.api import non_fieldset_fields
from collective.contact.duplicated.testing import IntegrationTestCase
from plone import api
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.dexterity.interfaces import IDexterityFTI
from z3c.relationfield.relation import RelationValue
from zope.component import getUtility
from zope.intid.interfaces import IIntIds


class TestApi(IntegrationTestCase):

    def setUp(self):
        super(TestApi, self).setUp()
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        login(self.portal, TEST_USER_NAME)
        self.directory = self.portal.mydirectory

    def test_non_fieldset_fields(self):
        person_schema = getUtility(IDexterityFTI, name="person").lookupSchema()
        self.assertEqual(non_fieldset_fields(person_schema)[:3], ["lastname", "firstname", "gender"])
        # every field of the IContactDetails behavior is in a fieldset
        self.assertEqual(non_fieldset_fields(IContactDetails), [])

    def test_get_fieldsets(self):
        fieldsets = get_fieldsets("person")
        self.assertEqual([fs["id"] for fs in fieldsets], ["default", "contact_details", "address"])
        default = fieldsets[0]
        self.assertEqual(default["title"], "Default")
        default_names = [f.__name__ for f in default["fields"]]
        # schema fields first, then the fields of the behaviors outside fieldsets
        self.assertEqual(default_names[:3], ["lastname", "firstname", "gender"])
        self.assertIn("birthday", default_names)
        self.assertIn("email", [f.__name__ for f in fieldsets[1]["fields"]])
        address_names = [f.__name__ for f in fieldsets[2]["fields"]]
        self.assertIn("city", address_names)
        # parent_address is excluded (computed from the parent organization)
        self.assertNotIn("parent_address", address_names)
        # held position: position is the first field
        self.assertEqual(get_fieldsets("held_position")[0]["fields"][0].__name__, "position")

    def test_get_fields(self):
        names = [f.__name__ for f in get_fields("person")]
        self.assertEqual(names, [f.__name__ for fs in get_fieldsets("person") for f in fs["fields"]])
        for name in ("lastname", "email", "city", "use_parent_address"):
            self.assertIn(name, names)
        self.assertNotIn("parent_address", names)

    def test_get_back_references(self):
        pepper = self.directory.pepper
        brigadelh = self.directory.armeedeterre.corpsa.divisionalpha.regimenth.brigadelh
        # no relation to the person
        self.assertEqual(get_back_references(pepper), [])
        # held position of rambo -> organization brigadelh (position field)
        self.assertEqual(
            get_back_references(brigadelh), [{"obj": self.directory.rambo.brigadelh, "attribute": "position"}]
        )
        # letter -> pepper (relatedItems field)
        intids = getUtility(IIntIds)
        letter = api.content.create(
            container=self.portal, type="letter", id="letter", relatedItems=[RelationValue(intids.getId(pepper))]
        )
        self.assertEqual(get_back_references(pepper), [{"obj": letter, "attribute": "relatedItems"}])
