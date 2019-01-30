# -*- coding: utf-8 -*-
from plone import api
from plone.api.exc import InvalidParameterError

try:
    from Products.CMFPlone.resources.browser.cook import cookWhenChangingSettings
except ImportError:
    cookWhenChangingSettings = None


def isNotCurrentProfile(context):
    return context.readDataFile("collectivecontactduplicated_marker.txt") is None


def post_install(context):
    """Post install script"""
    if isNotCurrentProfile(context):
        return


def refresh_resources(context):
    try:
        css_tool = api.portal.get_tool('portal_css')
    except InvalidParameterError:
        pass
    else:
        css_tool.cookResources()

    try:
        js_tool = api.portal.get_tool('portal_javascripts')

    except InvalidParameterError:
        pass
    else:
        js_tool.cookResources()

    if cookWhenChangingSettings is not None:  # Plone 5
        cookWhenChangingSettings(context)
