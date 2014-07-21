# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.interface import Interface


class ICollectiveContactDuplicatedLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IFieldRenderer(Interface):
    """Adapts a zope.schema field to render content on screen
    """

    def render(self, content):
        """Render field value on compare screen
        """


class IFieldValueCopy(Interface):
    """Adapts a zope.schema field to provide tool to transfer a value
    from a content to an other
    """

    def copy(self, source, target):
        """Transfer the field value from source object to target object
        """
