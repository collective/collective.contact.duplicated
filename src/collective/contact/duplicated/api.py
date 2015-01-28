from collections import OrderedDict

from Acquisition import aq_inner
from zope.intid.interfaces import IIntIds
from zope.component import getUtility
from zope.schema import getFieldsInOrder

from zc.relation.interfaces import ICatalog

from plone.autoform.interfaces import IFormFieldProvider
from plone.behavior.interfaces import IBehavior
from plone.dexterity.interfaces import IDexterityFTI
from plone.supermodel.interfaces import FIELDSETS_KEY

from collective.contact.duplicated import _


EXCLUDED_FIELDS = ['parent_address']

def _get_schema_fields(schema, names):
    return [schema[f] for f in names
            if f not in EXCLUDED_FIELDS
            and not schema[f].readonly]


def non_fieldset_fields(schema):
    fieldset_fields = []
    fieldsets = schema.queryTaggedValue(FIELDSETS_KEY, [])

    for fieldset in fieldsets:
        fieldset_fields.extend(fieldset.fields)

    fields = [info[0] for info in getFieldsInOrder(schema)]
    return [f for f in fields if f not in fieldset_fields]


def get_fieldsets(portal_type):
    fti = getUtility(IDexterityFTI, name=portal_type)
    schema = fti.lookupSchema()
    fieldsets_dict = OrderedDict({'default':
                                  {'id': 'default',
                                   'title': _(u'Default'),
                                   'fields': _get_schema_fields(schema,
                                                   non_fieldset_fields(schema))}
                                  })
    for fieldset in schema.queryTaggedValue(FIELDSETS_KEY, []):
        fieldsets_dict[fieldset.name] = {
                 'id': fieldset.__name__,
                 'title': fieldset.label,
                 'fields': _get_schema_fields(schema,
                                              fieldset.fields)
                 }

    for behavior_id in fti.behaviors:
        behavior = getUtility(IBehavior, behavior_id).interface
        if not IFormFieldProvider.providedBy(behavior):
            continue

        fieldsets_dict['default']['fields'].extend(
                    _get_schema_fields(behavior, non_fieldset_fields(behavior)))

        for fieldset in behavior.queryTaggedValue(FIELDSETS_KEY, []):
            fieldsets_dict.setdefault(fieldset.__name__,
                  {'id': fieldset.__name__,
                   'title': fieldset.label,
                   'fields': []})['fields'].extend(
                                 _get_schema_fields(behavior, fieldset.fields))

    return fieldsets_dict.values()


def get_fields(portal_type):
    fieldsets = get_fieldsets(portal_type)
    fields = []
    for fieldset in fieldsets:
        fields.extend(fieldset['fields'])

    return fields


def get_back_references(source_object):
    """ Return back references from source object on specified attribute_name """
    catalog = getUtility(ICatalog)
    intids = getUtility(IIntIds)
    source_intid = intids.getId(aq_inner(source_object))
    result = []
    for rel in catalog.findRelations({'to_id': source_intid}):
        from_id = getattr(rel, '_from_id', None)
        if not from_id:
            from_id = rel.from_id
        obj = intids.queryObject(from_id)
        if obj:
            result.append({'obj': obj,
                           'attribute': rel.from_attribute})
    return result
