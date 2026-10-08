# -*- coding: utf-8 -*-
"""Tests of browser/view.py: the merge-contacts (Compare) and merge-contacts-apply (Merge) views."""

from collective.contact.duplicated.api import get_back_references
from collective.contact.duplicated.browser.view import Compare
from collective.contact.duplicated.browser.view import Merge
from collective.contact.duplicated.interfaces import ICollectiveContactDuplicatedLayer
from collective.contact.duplicated.testing import IntegrationTestCase
from plone import api
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.uuid.interfaces import IUUID
from Products.statusmessages.interfaces import IStatusMessage
from z3c.relationfield.relation import RelationValue
from zExceptions import BadRequest
from zExceptions import NotFound
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.interface import alsoProvides
from zope.intid.interfaces import IIntIds

import json
import unittest


class ViewTestCase(IntegrationTestCase):

    def setUp(self):
        super(ViewTestCase, self).setUp()
        self.request = self.layer["request"]
        alsoProvides(self.request, ICollectiveContactDuplicatedLayer)
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        login(self.portal, TEST_USER_NAME)
        self.directory = self.portal.mydirectory
        self.degaulle = self.directory.degaulle
        self.pepper = self.directory.pepper
        self.degaulle_uid = IUUID(self.degaulle)
        self.pepper_uid = IUUID(self.pepper)

    def relation(self, obj):
        return RelationValue(getUtility(IIntIds).getId(obj))

    def compare(self, uids, data=None):
        self.request.form.clear()
        # request.get caches the form values in request.other
        for key in ("uids", "data"):
            self.request.other.pop(key, None)
        self.request.form["uids"] = uids
        if data is not None:
            self.request.form["data"] = data
        view = getMultiAdapter((self.directory, self.request), name="merge-contacts")
        self.assertIsInstance(view, Compare)
        return view

    def merge(self, **form):
        self.request.form.clear()
        self.request.form.update(form)
        view = getMultiAdapter((self.directory, self.request), name="merge-contacts-apply")
        self.assertIsInstance(view, Merge)
        return view

    def redirect_uids(self):
        """uids of the merge-contacts url the response redirects to"""
        location = self.request.response.getHeader("location")
        url, query = location.split("?")
        self.assertEqual(url, "http://nohost/plone/mydirectory/merge-contacts")
        params = [param.split("=") for param in query.split("&")]
        self.assertEqual(set(name for name, uid in params), {"uids:list"})
        return [uid for name, uid in params]

    def status_messages(self):
        return [m.message for m in IStatusMessage(self.request).show()]


class TestCompare(ViewTestCase):

    def test_escape(self):
        view = self.compare([self.degaulle_uid, self.pepper_uid])
        self.assertEqual(
            view.escape('<b>De Gaulle & "Pepper"</b>'), "&lt;b&gt;De Gaulle &amp; &quot;Pepper&quot;&lt;/b&gt;"
        )

    def test_get_contents(self):
        # two persons
        contents = self.compare([self.degaulle_uid, self.pepper_uid]).get_contents()
        self.assertEqual([c["uid"] for c in contents], [self.degaulle_uid, self.pepper_uid])
        self.assertEqual(contents[0]["obj"], self.degaulle)
        self.assertEqual(contents[0]["path"], "/plone/mydirectory/degaulle")
        self.assertEqual(contents[0]["back_references"], [])
        self.assertEqual(sorted(o.getId() for o in contents[0]["subcontents"]), ["adt", "gadt"])
        self.assertEqual([o.getId() for o in contents[1]["subcontents"]], ["sergent_pepper"])
        # back references of an organization
        brigadelh = self.directory.armeedeterre.corpsa.divisionalpha.regimenth.brigadelh
        regimenth = brigadelh.aq_parent
        contents = self.compare([IUUID(regimenth), IUUID(brigadelh)]).get_contents()
        self.assertEqual(
            contents[1]["back_references"], [{"obj": self.directory.rambo.brigadelh, "attribute": "position"}]
        )
        # one content and extra data: a temporary content
        adt_uid = IUUID(self.degaulle.adt)
        contents = self.compare([adt_uid, "TEMP"], data='{"label": "De Gaulle label"}').get_contents()
        self.assertEqual([c["uid"] for c in contents], [adt_uid, "TEMP"])
        self.assertEqual(contents[1]["obj"].label, "De Gaulle label")
        self.assertEqual(contents[1]["back_references"], [])
        self.assertEqual(contents[1]["subcontents"], [])
        # less than two contents
        self.assertRaises(BadRequest, self.compare([self.degaulle_uid]).get_contents)
        # unknown content
        self.assertRaises(NotFound, self.compare([self.degaulle_uid, "unknown-uid"]).get_contents)
        # contents of different types
        self.assertRaises(
            AssertionError, self.compare([self.degaulle_uid, IUUID(self.directory.armeedeterre)]).get_contents
        )

    def test_update(self):
        view = self.compare([self.degaulle_uid, self.pepper_uid])
        view.update()
        self.assertEqual(view.portal_type, "person")
        self.assertEqual([fs["id"] for fs in view.fieldsets], ["default", "contact_details", "address"])
        self.assertFalse(view.merge_hp_persons)
        # held positions of the same person
        view = self.compare([IUUID(self.degaulle.adt), IUUID(self.degaulle.gadt)])
        view.update()
        self.assertEqual(view.portal_type, "held_position")
        self.assertFalse(view.merge_hp_persons)
        # held positions of different persons: the persons can be merged too
        view = self.compare([IUUID(self.degaulle.adt), IUUID(self.pepper.sergent_pepper)])
        view.update()
        self.assertTrue(view.merge_hp_persons)
        self.assertEqual(
            view.merge_person_url,
            "http://nohost/plone/mydirectory/merge-contacts?uids:list={}&uids:list={}".format(
                self.degaulle_uid, self.pepper_uid
            ),
        )
        # a held position and extra data
        view = self.compare([IUUID(self.degaulle.adt), "TEMP"], data='{"label": "De Gaulle label"}')
        view.update()
        self.assertFalse(view.merge_hp_persons)

    def test_diff(self):
        self.degaulle.firstname = "<b>Charles</b>"
        view = self.compare([self.degaulle_uid, self.pepper_uid])
        view.update()
        fields = dict((f.__name__, f) for fs in view.fieldsets for f in fs["fields"])
        # different values: the first one is selected
        self.assertEqual(
            view.diff(fields["lastname"]),
            [
                {
                    "uid": self.degaulle_uid,
                    "value": "De Gaulle",
                    "render": "De Gaulle",
                    "differing": True,
                    "selectable": True,
                    "selected": True,
                },
                {
                    "uid": self.pepper_uid,
                    "value": "Pepper",
                    "render": "Pepper",
                    "differing": True,
                    "selectable": True,
                    "selected": False,
                },
            ],
        )
        # set on one content only: the set value is selected
        self.assertEqual(
            view.diff(fields["phone"]),
            [
                {
                    "uid": self.degaulle_uid,
                    "value": None,
                    "render": None,
                    "differing": True,
                    "selectable": False,
                    "selected": False,
                },
                {
                    "uid": self.pepper_uid,
                    "value": "0288443344",
                    "render": "0288443344",
                    "differing": True,
                    "selectable": True,
                    "selected": True,
                },
            ],
        )
        # same value: nothing to select
        self.assertEqual(
            [(d["render"], d["differing"], d["selectable"], d["selected"]) for d in view.diff(fields["gender"])],
            [("Male", False, False, False), ("Male", False, False, False)],
        )
        # set on no content
        self.assertIsNone(view.diff(fields["fax"]))
        # the rendering is escaped
        self.assertEqual(view.diff(fields["firstname"])[0]["render"], "&lt;b&gt;Charles&lt;/b&gt;")
        # less than two contents
        view.contents = view.contents[:1]
        self.assertIsNone(view.diff(fields["lastname"]))
        # the position rendering is html (not escaped)
        view = self.compare([IUUID(self.degaulle.adt), IUUID(self.pepper.sergent_pepper)])
        view.update()
        position = view.diff(view.fieldsets[0]["fields"][0])
        self.assertTrue(position[0]["render"].startswith('<a href="http://nohost/plone/mydirectory/armeedeterre"'))

    def test___call__(self):
        brigadelh = self.directory.armeedeterre.corpsa.divisionalpha.regimenth.brigadelh
        html = self.compare([self.degaulle_uid, self.pepper_uid])()
        self.assertIn('action="http://nohost/plone/mydirectory/merge-contacts-apply"', html)
        for uid in (self.degaulle_uid, self.pepper_uid):
            self.assertIn('value="{}"'.format(uid), html)
            self.assertIn('id="path-{}"'.format(uid), html)
            self.assertIn('id="lastname-{}"'.format(uid), html)
        self.assertIn("/plone/mydirectory/degaulle", html)
        self.assertIn("Mister Pepper", html)
        # subcontents of both persons can be selected to be merged
        self.assertIn('name="subcontent_uids:list"', html)
        self.assertNotIn('id="hp-person-merge"', html)
        # held positions of different persons
        html = self.compare([IUUID(self.degaulle.adt), IUUID(self.pepper.sergent_pepper)])()
        self.assertIn('id="hp-person-merge"', html)
        self.assertIn('name="merge-hp-persons"', html)
        self.assertIn('href="http://nohost/plone/mydirectory/merge-contacts?uids:list=', html)
        # back references of an organization
        html = self.compare([IUUID(brigadelh.aq_parent), IUUID(brigadelh)])()
        self.assertIn('href="http://nohost/plone/mydirectory/rambo/brigadelh"', html)
        self.assertIn("held_position - position", html)


class TestMerge(ViewTestCase):

    def test__transfer_field_values(self):
        view = self.merge()
        contents = {
            self.degaulle_uid: self.degaulle,
            self.pepper_uid: self.pepper,
            "TEMP": {"email": "charles@elysee.fr"},
        }
        values = {
            "_authenticator": "secret",
            "ajax_load": "1",
            "data": "{}",
            "lastname": self.degaulle_uid,  # canonical value kept
            "country": self.pepper_uid,  # value of another content
            "city": "empty",  # emptied
            "fax": "empty",  # already empty
            "email": "TEMP",
        }  # extra data value
        view._transfer_field_values(values, contents, self.degaulle)
        self.assertEqual(self.degaulle.lastname, "De Gaulle")
        self.assertEqual(self.degaulle.country, "England")
        self.assertIsNone(self.degaulle.city)
        self.assertIsNone(self.degaulle.fax)
        self.assertEqual(self.degaulle.email, "charles@elysee.fr")
        self.assertEqual(self.pepper.country, "England")

    def test__transfer_back_references(self):
        view = self.merge()
        letter1 = api.content.create(
            container=self.portal, type="letter", id="letter1", relatedItems=[self.relation(self.pepper)]
        )
        letter2 = api.content.create(
            container=self.portal,
            type="letter",
            id="letter2",
            relatedItems=[self.relation(self.pepper), self.relation(self.degaulle)],
        )
        view._transfer_back_references(self.pepper, self.degaulle)
        self.assertEqual([r.to_object for r in letter1.relatedItems], [self.degaulle])
        # no duplicated relation
        self.assertEqual([r.to_object for r in letter2.relatedItems], [self.degaulle])
        self.assertEqual(get_back_references(self.pepper), [])
        self.assertEqual(sorted(r["obj"].getId() for r in get_back_references(self.degaulle)), ["letter1", "letter2"])
        # single relation (position of a held position)
        brigadelh = self.directory.armeedeterre.corpsa.divisionalpha.regimenth.brigadelh
        regimenth = brigadelh.aq_parent
        view._transfer_back_references(brigadelh, regimenth)
        self.assertEqual(self.directory.rambo.brigadelh.position.to_object, regimenth)

    def test__remove_content_object(self):
        view = self.merge()
        letter = api.content.create(
            container=self.portal, type="letter", id="letter", relatedItems=[self.relation(self.pepper)]
        )
        view._remove_content_object(self.pepper, self.degaulle)
        self.assertNotIn("pepper", self.directory)
        # subcontents moved into the canonical content
        self.assertEqual(sorted(self.degaulle.objectIds()), ["adt", "gadt", "sergent_pepper"])
        self.assertEqual(letter.relatedItems[0].to_object, self.degaulle)
        self.assertEqual(self.status_messages(), ["/plone/mydirectory/pepper has been removed"])

    def test___call__(self):
        # persons: redirect to the canonical content
        self.merge(
            uids=[self.degaulle_uid, self.pepper_uid],
            path=self.degaulle_uid,
            country=self.pepper_uid,
            lastname=self.degaulle_uid,
        )()
        self.assertEqual(self.request.response.getHeader("location"), "http://nohost/plone/mydirectory/degaulle")
        self.assertEqual(self.degaulle.country, "England")
        self.assertNotIn("pepper", self.directory)
        self.assertIn("sergent_pepper", self.degaulle)
        self.assertEqual(self.status_messages(), ["/plone/mydirectory/pepper has been removed"])
        # extra data
        adt_uid = IUUID(self.degaulle.adt)
        self.merge(uids=[adt_uid, "TEMP"], path=adt_uid, label="TEMP", data=json.dumps({"label": "Émissaire"}))()
        self.assertEqual(self.degaulle.adt.label, "Émissaire")
        self.assertEqual(self.request.response.getHeader("location"), "http://nohost/plone/mydirectory/degaulle/adt")
        # held positions of different persons, with merge-hp-persons: redirect to the merge of the persons
        rambo = self.directory.rambo
        draper = self.directory.draper
        captain_uid = IUUID(draper.captain_crunch)
        self.merge(**{"uids": [IUUID(rambo.brigadelh), captain_uid], "path": captain_uid, "merge-hp-persons": "1"})()
        self.assertNotIn("brigadelh", rambo)
        self.assertEqual(sorted(self.redirect_uids()), sorted([IUUID(rambo), IUUID(draper)]))
        # subcontents selected: redirect to the merge of the subcontents
        subcontent_uids = [IUUID(draper.divisionbeta), captain_uid]
        self.merge(uids=[IUUID(rambo), IUUID(draper)], path=IUUID(draper), subcontent_uids=subcontent_uids)()
        self.assertNotIn("rambo", self.directory)
        self.assertEqual(self.redirect_uids(), subcontent_uids)

    @unittest.expectedFailure
    def test___call___unknown_content(self):
        """Plone 4 bug: BadRequest is instantiated but not raised (AttributeError/TypeError later)"""
        view = self.merge(uids=[self.degaulle_uid, "unknown-uid"], path=self.degaulle_uid)
        self.assertRaises(BadRequest, view)

    @unittest.expectedFailure
    def test___call___unknown_canonical(self):
        """Plone 4 bug: BadRequest is instantiated but not raised (AttributeError later)"""
        view = self.merge(uids=[self.degaulle_uid, self.pepper_uid], path="unknown-uid")
        self.assertRaises(BadRequest, view)
