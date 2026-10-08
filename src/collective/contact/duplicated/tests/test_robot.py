# -*- coding: utf-8 -*-
"""Robot suites of tests/robot, run with the layer of their file name.

ROBOT_PLONE_MAJOR (4 or 6) selects the UI keywords: robotsuite passes the
ROBOT_* environment variables to the suites as robot variables.
"""
from ..testing import ACCEPTANCE
from ..testing import FACETED_ACCEPTANCE
from importlib.metadata import version
from plone.testing import layered

import os
import robotsuite
import unittest


# suites needing an optional integration layer, e.g. {'test_facetednav.robot': ADDONS_ACCEPTANCE}
SUITE_LAYERS = {"test_facetednav.robot": FACETED_ACCEPTANCE}

# suites skipped on Plone 6: collective.contact.facetednav (plone6 branch, not migrated yet) @@faceted_query
# template still uses here/global_defines (KeyError on Plone 6), so the faceted results never load
PLONE4_ONLY = {"test_facetednav.robot"}


def test_suite():
    os.environ.setdefault("ROBOT_PLONE_MAJOR", version("Products.CMFPlone").split(".")[0])
    suite = unittest.TestSuite()
    robot_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "robot")
    for name in sorted(os.listdir(robot_dir)):
        if name.startswith("test_") and name.endswith(".robot"):
            if name in PLONE4_ONLY and os.environ["ROBOT_PLONE_MAJOR"] != "4":
                continue
            suite.addTests(
                [
                    layered(
                        robotsuite.RobotTestSuite(os.path.join("robot", name)), layer=SUITE_LAYERS.get(name, ACCEPTANCE)
                    ),
                ]
            )
    return suite
