# -*- coding: utf-8 -*-
"""Installer for the collective.contact.duplicated package."""

from setuptools import find_packages
from setuptools import setup


long_description = (
    open('README.rst').read()
    + '\n' +
    'Contributors\n'
    '============\n'
    + '\n' +
    open('CONTRIBUTORS.rst').read()
    + '\n' +
    open('CHANGES.rst').read()
    + '\n')


setup(
    name='collective.contact.duplicated',
    version='0.7.dev0',
    description="Tools to manage duplicated contacts",
    long_description=long_description,
    # Get more from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 4.3",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
    ],
    keywords='contacts',
    author='Thomas Desvenain',
    author_email='thomas.desvenain@gmail.com',
    url='http://pypi.python.org/pypi/collective.contact.duplicated',
    license='GPL',
    packages=find_packages('src', exclude=['ez_setup']),
    namespace_packages=['collective', 'collective.contact'],
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'collective.contact.core',
        'collective.contact.facetednav',
        'future',
        'plone.api',
        'setuptools',
    ],
    extras_require={
        'test': [
            'ecreall.helpers.testing',
            'collective.contact.facetednav',
            'plone.app.testing',
            'plone.app.robotframework',
        ],
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
