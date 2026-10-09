# -*- coding: utf-8 -*-
"""Base module for unittesting."""

from collective.contact.facetednav.interfaces import IActionsEnabled
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import login
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.testing.zope import installProduct
from plone.testing.zope import uninstallProduct
from plone.testing.zope import WSGI_SERVER_FIXTURE as SERVER_FIXTURE
from zope.globalrequest import clearRequest
from zope.globalrequest import setLocal
from zope.interface import alsoProvides

import collective.contact.core
import collective.contact.duplicated
import collective.contact.facetednav
import collective.js.backbone
import os
import transaction
import unittest


FACETED_XML = os.path.join(os.path.dirname(__file__), "tests", "faceted.xml")


class CollectiveContactDuplicatedLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)
    products = ("collective.contact.duplicated",)

    def setUpZope(self, app, configurationContext):
        """Set up Zope."""
        # Load ZCML
        self.loadZCML(package=collective.contact.duplicated, name="testing.zcml")
        for p in self.products:
            installProduct(app, p)
        self.loadZCML(package=collective.contact.core, name="testing.zcml")

    def setUpPloneSite(self, portal):
        """Set up Plone."""
        setLocal("request", portal.REQUEST)  # collective.fingerpointing (imio.fpaudit) needs a request
        # Install into Plone site using portal_setup
        applyProfile(portal, "collective.contact.core:testing")
        # insert some test data
        applyProfile(portal, "collective.contact.core:test_data")
        applyProfile(portal, "collective.contact.duplicated:testing")

        # Login and create some test content
        setRoles(portal, TEST_USER_ID, ["Manager"])
        login(portal, TEST_USER_NAME)
        folder_id = portal.invokeFactory("Folder", "folder")
        portal[folder_id].reindexObject()

        # Commit so that the test browser sees these objects
        transaction.commit()
        clearRequest()  # else the next layers get a request bound to a closed connection

    def tearDownZope(self, app):
        """Tear down Zope."""
        for p in reversed(self.products):
            uninstallProduct(app, p)


FIXTURE = CollectiveContactDuplicatedLayer(name="FIXTURE")


INTEGRATION = IntegrationTesting(bases=(FIXTURE,), name="INTEGRATION")


FUNCTIONAL = FunctionalTesting(bases=(FIXTURE,), name="FUNCTIONAL")


ACCEPTANCE = FunctionalTesting(bases=(FIXTURE, REMOTE_LIBRARY_BUNDLE_FIXTURE, SERVER_FIXTURE), name="ACCEPTANCE")


class FacetedLayer(PloneSandboxLayer):
    """collective.contact.facetednav integration: mydirectory is a faceted
    directory listing the persons, with the contact actions enabled."""

    defaultBases = (FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # collective.contact.facetednav (plone6 branch) depends on the collective.js.backbone profile
        # without including its ZCML: z3c.autoinclude doesn't run in test layers
        self.loadZCML(package=collective.js.backbone)
        self.loadZCML(package=collective.contact.facetednav)
        installProduct(app, "collective.contact.facetednav")

    def setUpPloneSite(self, portal):
        setLocal("request", portal.REQUEST)
        applyProfile(portal, "collective.contact.facetednav:default")
        directory = portal.mydirectory
        directory.unrestrictedTraverse("@@faceted_subtyper").enable()
        with open(FACETED_XML, "rb") as import_file:
            directory.unrestrictedTraverse("@@faceted_exportimport")._import_xml(import_file=import_file)
        alsoProvides(directory, IActionsEnabled)
        transaction.commit()
        clearRequest()

    def tearDownZope(self, app):
        uninstallProduct(app, "collective.contact.facetednav")


FACETED_FIXTURE = FacetedLayer(name="FACETED_FIXTURE")


FACETED_INTEGRATION = IntegrationTesting(bases=(FACETED_FIXTURE,), name="FACETED_INTEGRATION")


FACETED_ACCEPTANCE = FunctionalTesting(
    bases=(FACETED_FIXTURE, REMOTE_LIBRARY_BUNDLE_FIXTURE, SERVER_FIXTURE), name="FACETED_ACCEPTANCE"
)


class IntegrationTestCase(unittest.TestCase):
    """Base class for integration tests."""

    layer = INTEGRATION

    def setUp(self):
        super(IntegrationTestCase, self).setUp()
        self.portal = self.layer["portal"]


class FunctionalTestCase(unittest.TestCase):
    """Base class for functional tests."""

    layer = FUNCTIONAL
