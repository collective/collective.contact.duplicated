# -*- coding: utf-8 -*-
"""Setup/installation tests for this package."""

from collective.contact.duplicated.interfaces import ICollectiveContactDuplicatedLayer
from collective.contact.duplicated.testing import IntegrationTestCase
from plone.base.utils import get_installer
from plone.browserlayer import utils
from plone.registry.interfaces import IRegistry
from zope.component import getUtility


PACKAGE = "collective.contact.duplicated"
JS = "++resource++collective.contact.duplicated/duplicated.js"
CSS = "++resource++collective.contact.duplicated/duplicated.css"


def is_installed(portal, product):
    return get_installer(portal).is_product_installed(product)


def uninstall(portal, product):
    get_installer(portal).uninstall_product(product)


def registered_resources(portal):
    """css and js of the registry bundles"""
    registry = getUtility(IRegistry)
    return set(
        registry[name]
        for name in registry.records.keys()
        if name.startswith("plone.bundles/") and name.endswith("compilation")
    )


class TestInstall(IntegrationTestCase):
    """Test installation of collective.contact.duplicated into Plone."""

    def test_product_installed(self):
        self.assertTrue(is_installed(self.portal, PACKAGE))
        # metadata.xml dependency
        self.assertTrue(is_installed(self.portal, "collective.contact.core"))

    # browserlayer.xml
    def test_browserlayer(self):
        self.assertIn(ICollectiveContactDuplicatedLayer, utils.registered_layers())

    # registry.xml
    def test_resources(self):
        resources = registered_resources(self.portal)
        self.assertIn(JS, resources)
        self.assertIn(CSS, resources)

    def test_uninstall(self):
        uninstall(self.portal, PACKAGE)
        self.assertFalse(is_installed(self.portal, PACKAGE))
        self.assertNotIn(ICollectiveContactDuplicatedLayer, utils.registered_layers())
        resources = registered_resources(self.portal)
        self.assertNotIn(JS, resources)
        self.assertNotIn(CSS, resources)
