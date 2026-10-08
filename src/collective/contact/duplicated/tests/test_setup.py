# -*- coding: utf-8 -*-
"""Setup/installation tests for this package."""

from collective.contact.duplicated.interfaces import ICollectiveContactDuplicatedLayer
from collective.contact.duplicated.testing import IntegrationTestCase
from plone import api
from plone.base.utils import get_installer
from plone.browserlayer import utils


class TestInstall(IntegrationTestCase):
    """Test installation of collective.contact.duplicated into Plone."""

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        self.installer = get_installer(self.portal, self.layer["request"])

    def test_product_installed(self):
        """Test if collective.contact.duplicated is installed."""
        self.assertTrue(self.installer.is_product_installed("collective.contact.duplicated"))

    def test_uninstall(self):
        """Test if collective.contact.duplicated is cleanly uninstalled."""
        self.installer.uninstall_product("collective.contact.duplicated")
        self.assertFalse(self.installer.is_product_installed("collective.contact.duplicated"))
        self.assertNotIn(ICollectiveContactDuplicatedLayer, utils.registered_layers())
        self.assertIsNone(
            api.portal.get_registry_record("plone.bundles/collective-contact-duplicated.enabled", default=None)
        )

    # browserlayer.xml
    def test_browserlayer(self):
        """Test that ICollectiveContactDuplicatedLayer is registered."""
        self.assertIn(ICollectiveContactDuplicatedLayer, utils.registered_layers())
