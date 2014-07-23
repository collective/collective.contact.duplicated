# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.interface import Interface


class ICollectiveContactDuplicatedLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IFieldDiff(Interface):
    """Adapts a zope.schema field to provide diff helpers
    """

    def is_different(self, value1, value2):
        """Returns True or any information if value1 and value2 differ
        return False if value1 and value2 are equal
        """

    def render(self, content):
        """Render field value on compare screen
        """

    def copy(self, source, target):
        """Transfer the field value from source object to target object
        """
