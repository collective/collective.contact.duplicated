from collections import OrderedDict, Counter

from zExceptions import NotFound
from zope.component import getUtility
from Products.Five.browser import BrowserView
from plone.schemaeditor.utils import non_fieldset_fields
from plone.dexterity.interfaces import IDexterityFTI

from plone import api
from plone.behavior.interfaces import IBehavior
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel.interfaces import FIELDSETS_KEY
from plone.uuid.interfaces import IUUID


class Compare(BrowserView):

    def get_contents(self):
        uids = self.request['uids']
        contents = api.portal.get_tool('portal_catalog')(UID=uids)
        if len(contents) != len(uids):
            raise NotFound

        # one content type
        assert len([b.portal_type for b in b in contents]) == 1
        return [{'obj': c.getObject(),
                 'uid': c.UID,
                 'path': c.getPath()} for c in contents]

    def get_fieldsets(self, portal_type):
        fti = getUtility(IDexterityFTI, name=portal_type)
        schema = fti.lookupSchema()
        fieldsets = []
        fieldsets_dict = OrderedDict({'default':
                                      {'title': '',
                                       'fields': non_fieldset_fields(schema)}})
        for fieldset in schema.queryTaggedValue(FIELDSETS_KEY, []):
            fieldsets_dict[fieldset.name] = {'title': fieldset.name,
                                             'fields': [schema.getField(f)
                                                        for f in fieldset.fields]}
        self.fieldsets = fieldsets

        for behavior_id in fti.behaviors:
            schema = getUtility(IBehavior, behavior_id).interface
            if not IFormFieldProvider.providedBy(schema):
                continue

            for fieldset in schema.queryTaggedValue(FIELDSETS_KEY, []):
                fieldsets.setdefault(fieldset.__name__, []).extend(fieldset.fields)

            fieldsets['default'].extend(non_fieldset_fields(schema))


    def update(self):
        self.contents = self.get_contents()
        self.fieldsets = self.get_fieldsets(self.contents[0].portal_type)

    def diff(self, field):
        for content in self.contents:
            diff = [{'uid': content['uid'],
                     'value': getattr(content, field.__name__)}
                    for content in self.contents]

        if Counter([v['value'] for v in diff]) == 1:
            return None


    def __call__(self):
        self.update()
        super(Compare, self).__call__()