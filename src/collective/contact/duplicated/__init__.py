# -*- coding: utf-8 -*-
"""Init and utils."""

from zope.i18nmessageid import MessageFactory

import logging


_ = MessageFactory('collective.contact.duplicated')
logger = logging.getLogger('collective.contact.duplicated')


def initialize(context):
    """Initializer called when used as a Zope 2 product."""
