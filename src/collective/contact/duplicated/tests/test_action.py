# -*- coding: utf-8 -*-
"""Tests of browser/contactfaceted/action.py: the "Merge duplicated" batch action of collective.contact.facetednav."""

from collective.contact.duplicated.browser.contactfaceted.action import MergeAction
from collective.contact.duplicated.interfaces import ICollectiveContactDuplicatedLayer
from collective.contact.duplicated.testing import FACETED_INTEGRATION
from collective.contact.facetednav.interfaces import ICollectiveContactFacetednavLayer
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from Products.Five.browser import BrowserView
from zope.component import getMultiAdapter
from zope.interface import alsoProvides
from zope.viewlet.interfaces import IViewletManager

import unittest


class TestMergeAction(unittest.TestCase):

    layer = FACETED_INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        alsoProvides(self.request, ICollectiveContactFacetednavLayer, ICollectiveContactDuplicatedLayer)
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        login(self.portal, TEST_USER_NAME)
        directory = self.portal.mydirectory
        self.manager = getMultiAdapter(
            (directory, self.request, BrowserView(directory, self.request)),
            IViewletManager,
            name="collective.contact.facetednav.batchactions",
        )
        self.manager.update()

    def viewlet(self):
        viewlets = [
            v for v in self.manager.viewlets if v.__name__ == "collective.contact.duplicated.facetednav.actions.merge"
        ]
        self.assertEqual(len(viewlets), 1)
        return viewlets[0]

    def test_onclick(self):
        viewlet = self.viewlet()
        self.assertIsInstance(viewlet, MergeAction)
        self.assertEqual(viewlet.onclick, "contactduplicated.merge_contacts()")
        self.assertEqual(viewlet.name, "merge")
        self.assertTrue(viewlet.multiple_selection)
        # button of the batch actions: enabled when several contacts are selected
        html = viewlet.render()
        self.assertIn('id="contact-facetednav-action-merge"', html)
        self.assertIn('onclick="contactduplicated.merge_contacts()"', html)
        self.assertIn('value="Merge duplicated"', html)
        self.assertIn("multiple-selection", html)
