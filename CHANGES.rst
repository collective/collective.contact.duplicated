Changelog
=========


0.4 (2017-10-03)
----------------

- Handle when field value is a ComputedAttribute (from an acqproperty)
  [thomasdesvenain]

- Do not dismiss merge if only one UID + data
  [ebrehault]

- Avoid error with field using plone.app.vocabularies
  [sgeulette]

- Do merge action with Manager role to avoid security problems
  [sgeulette]

0.3.1 (2017-02-09)
------------------

- Prevent fatal error when a back reference relation to a duplicated contact
  is out of sync with any actual content.
  [thomasdesvenain]

- Prefer a 400 error than a 500 when user directly access to merge page without accurate params.
  [thomasdesvenain]

0.3.0 (2016-09-23)
------------------

- Merge contacts with data
  [simon-previdente]


0.2 (2015-11-24)
----------------

- Fix plone.protect compliancy
  [ebrehault]

- Fix permission: anybody allowed to add contacts must be able to merge
  duplicates
  [ebrehault]


0.1 (2015-06-02)
----------------

- Initial release.
  [tdesvenain]
