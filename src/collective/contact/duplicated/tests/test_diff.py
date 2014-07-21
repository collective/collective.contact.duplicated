# -*- coding: utf-8 -*-
"""Setup/installation tests for this package."""

from collective.contact.duplicated.testing import IntegrationTestCase
from plone import api


class TestInstall(IntegrationTestCase):
    """Test installation of collective.contact.duplicated into Plone."""
