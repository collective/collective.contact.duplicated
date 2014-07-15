# -*- coding: utf-8 -*-
"""Setup/installation tests for this package."""

from collective.contact.duplicated.testing import IntegrationTestCase
from plone import api


class TestInstall(IntegrationTestCase):
    """Test installation of collective.contact.duplicated into Plone."""

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if collective.contact.duplicated is installed with portal_quickinstaller."""
        self.assertTrue(self.installer.isProductInstalled('collective.contact.duplicated'))

    def test_uninstall(self):
        """Test if collective.contact.duplicated is cleanly uninstalled."""
        self.installer.uninstallProducts(['collective.contact.duplicated'])
        self.assertFalse(self.installer.isProductInstalled('collective.contact.duplicated'))

    # browserlayer.xml
    def test_browserlayer(self):
        """Test that ICollectiveContactDuplicatedLayer is registered."""
        from collective.contact.duplicated.interfaces import ICollectiveContactDuplicatedLayer
        from plone.browserlayer import utils
        self.assertIn(ICollectiveContactDuplicatedLayer, utils.registered_layers())
