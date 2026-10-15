"""Installer for the collective.contact.duplicated package."""

from setuptools import setup

long_description = (
    open("README.rst").read() + "\n" + "Contributors\n"
    "============\n"
    + "\n"
    + open("CONTRIBUTORS.rst").read()
    + "\n"
    + open("CHANGES.rst").read()
    + "\n"
)


setup(
    name="collective.contact.duplicated",
    version="1.0.0.dev0",
    description="Tools to manage duplicated contacts",
    long_description=long_description,
    # Get more from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 6.1",
        "Framework :: Plone :: 6.2",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
    ],
    keywords="contacts",
    author="Thomas Desvenain",
    author_email="thomas.desvenain@gmail.com",
    url="http://pypi.python.org/pypi/collective.contact.duplicated",
    license="GPL",
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.10",
    install_requires=[
        "collective.contact.core",
        "collective.contact.facetednav",
        "collective.contact.widget",
        "collective.z3cform.datagridfield",
        "plone.api",
        "plone.app.relationfield",
        "plone.app.textfield",
        "plone.autoform",
        "plone.behavior",
        "plone.dexterity",
        "plone.namedfile",
        "plone.schemaeditor",
        "plone.supermodel",
        "plone.uuid",
        "Products.CMFCore",
        "Products.GenericSetup",
        "Products.statusmessages",
        "z3c.form",
        "z3c.relationfield",
        "zc.relation",
        "Zope",
        "zope.intid",
    ],
    extras_require={
        "test": [
            "ecreall.helpers.testing",
            "plone.app.robotframework",
            "plone.app.testing",
            "plone.base",
            "plone.browserlayer",
            "plone.registry",
            "plone.testing",
            "Products.CMFPlone",
            "robotsuite",
        ],
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
