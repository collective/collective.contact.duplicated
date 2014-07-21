# -*- coding: utf-8 -*-
"""Setup/installation tests for this package."""

from zope.component import getUtility
from zope.intid.interfaces import IIntIds
from collective.contact.duplicated.testing import IntegrationTestCase
from plone import api
from plone.app.testing.helpers import login
from plone.app.testing.interfaces import TEST_USER_NAME
from plone.uuid.interfaces import IUUID
from z3c.relationfield.relation import RelationValue
from collective.contact.duplicated.api import get_back_references


class TestDiff(IntegrationTestCase):
    """Test installation of collective.contact.duplicated into Plone."""

    def test_diff(self):
        portal = self.layer['portal']
        login(portal, TEST_USER_NAME)

        degaulle = portal.mydirectory.degaulle
        pepper = portal.mydirectory.pepper

        # create a relation
        intids = getUtility(IIntIds)
        letter = api.content.create(type='letter', id='letter',
                                    container=portal,
                                    relatedItems=[RelationValue(intids.getId(pepper))])
        self.assertEqual(get_back_references(pepper),
                         [{'obj': letter, 'attribute': 'relatedItems'}])

        degaulle_uid = IUUID(degaulle)
        pepper_uid = IUUID(pepper)
        portal.REQUEST['uids'] = [degaulle_uid, pepper_uid]
        view = portal.mydirectory.unrestrictedTraverse('merge-contacts')
        view.update()
        fieldsets = view.fieldsets
        self.assertListEqual([fs['id'] for fs in fieldsets],
                             ['default', 'contact_details', 'address'])

        # different on each content
        self.assertEqual(view.diff(view.fieldsets[0]['fields'][0]),
            [{'differing': True,
              'render': u'De Gaulle',
              'selectable': True,
              'selected': True,
              'uid': degaulle_uid,
              'value': u'De Gaulle'},
             {'differing': True,
              'render': u'Pepper',
              'selectable': True,
              'selected': False,
              'uid': pepper_uid,
              'value': u'Pepper'}]
            )

        # similar on each content
        self.assertEqual(view.diff(view.fieldsets[0]['fields'][2]),
            [{'differing': False,
              'render': u'Male',
              'selectable': False,
              'selected': False,
              'uid': degaulle_uid,
              'value': u'M'},
             {'differing': False,
              'render': u'Male',
              'selectable': False,
              'selected': False,
              'uid': pepper_uid,
              'value': u'M'}])

        # unset on each content
        self.assertEqual(view.diff(view.fieldsets[0]['fields'][4]), None)

        view.get_contents()
        portal.REQUEST.form['uids'] = [degaulle_uid, pepper_uid]
        portal.REQUEST.form['path'] = degaulle_uid
        portal.REQUEST.form['country'] = pepper_uid
        portal.REQUEST.form['city'] = 'empty'
        view = portal.mydirectory.unrestrictedTraverse('merge-contacts-apply')()

        self.assertEqual(degaulle.country, 'England')
        self.assertEqual(degaulle.firstname, 'Charles')
        self.assertEqual(degaulle.city, None)

        # relations to pepper has been updated
        self.assertEqual(letter.relatedItems[0].to_object, degaulle)

        # pepper has been removed
        self.assertNotIn('pepper', portal.mydirectory)
        # and its held_positions has been moved in canonical
        self.assertIn('sergent_pepper', degaulle)