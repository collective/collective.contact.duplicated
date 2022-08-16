from collections import namedtuple
from collective.contact.core.content.held_position import IHeldPosition
from collective.contact.duplicated.api import get_back_references
from collective.contact.duplicated.api import get_fields
from collective.contact.duplicated.api import get_fieldsets
from collective.contact.duplicated.interfaces import IFieldDiff
from copy import copy
from plone import api
from plone.uuid.interfaces import IUUID
from Products.Five.browser import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form.interfaces import NO_VALUE
from z3c.relationfield.relation import RelationValue
from zExceptions import BadRequest
from zExceptions import NotFound
from zope.component import getUtility
from zope.intid.interfaces import IIntIds
from zope.lifecycleevent import modified

import html
import json


class Compare(BrowserView):

    contents = None
    portal_type = None
    fieldsets = None

    def escape(self, content):
        return html.escape(content)

    def get_contents(self):
        uids = copy(self.request['uids'])
        extra = self.request.get('data', None)
        counts = len(uids)
        if extra:
            counts += 1
        if counts < 2:
            raise BadRequest("You must select at least two contents")
        if 'TEMP' in uids:
            uids.remove('TEMP')

        contents = api.portal.get_tool('portal_catalog')(UID=uids)
        if len(contents) != len(uids):
            raise NotFound

        # one content type
        assert len(set([b.portal_type for b in contents])) == 1
        content_objs = [c.getObject() for c in contents]

        data = [{'obj': obj,
                 'uid': IUUID(obj),
                 'path': '/'.join(obj.getPhysicalPath()),
                 'back_references': get_back_references(obj),
                 'subcontents': obj.values()} for obj in content_objs]
        # add extra data as temporary object
        if extra:
            extra = json.loads(extra)
            data_obj = namedtuple('mystruct', extra.keys())(**extra)
            data.append({
                'obj': data_obj,
                'uid': 'TEMP',
                'back_references': [],
                'subcontents': [],
            })
        return data

    def update(self):
        self.contents = self.get_contents()
        first = self.contents[0]['obj']
        self.portal_type = first.portal_type
        self.fieldsets = get_fieldsets(self.portal_type)
        # check if this is contacts from different persons,
        # then we can also merge the persons
        self.merge_hp_persons = False
        if IHeldPosition.providedBy(first):
            person_uids = []
            for hp in self.contents:
                if hp['uid'] != 'TEMP':
                    person_uids.append(IUUID(hp['obj'].get_person()))

            if len(set(person_uids)) > 1:
                self.merge_hp_persons = True
                self.merge_person_url = "%s/merge-contacts?%s" % (
                    self.context.absolute_url(),
                    '&'.join(['uids:list=%s' % uid for uid in person_uids]))

    def diff(self, field):
        field_diff = IFieldDiff(field)
        if len(self.contents) < 2:
            return None

        values = [getattr(c['obj'], field.__name__, None)
                  for c in self.contents]

        #  check if at least two values differ
        value = None
        for index, value in enumerate(values[:-1]):
            if field_diff.is_different(value, values[index + 1]):
                differing = True
                break
        else:
            if value:  # set and all the same
                differing = False
            else:  # not set
                return None

        diff = []
        one_selected = False  # we select by default the first value that is set
        for index, content in enumerate(self.contents):
            value = values[index]
            render = field_diff.render(content['obj'])
            if render and field.__name__ not in ('activity', 'position'):  # do not break real html
                render = self.escape(render)
            if render is None or render == '':
                selectable = False
                selected = False
            elif not differing:
                selectable = False
                selected = False
            elif not one_selected:
                selected = True
                selectable = True
                one_selected = True
            else:
                selectable = True
                selected = False

            info = {'uid': content['uid'],
                    'value': value,
                    'selected': selected,
                    'differing': differing,
                    'selectable': selectable,
                    'render': render}
            diff.append(info)

        return diff


class Merge(BrowserView):

    def _transfer_field_values(self, values, contents, canonical):
        fields = dict([(field.__name__, field)
                       for field in get_fields(canonical.portal_type)])
        canonical_uid = IUUID(canonical)
        for field_name, uid in values.items():
            if field_name in ['_authenticator', 'data', 'ajax_load']:
                continue
            if uid == canonical_uid:
                continue
            elif uid == 'empty' and getattr(canonical, field_name, None) not in [NO_VALUE, None]:
                delattr(canonical, field_name)
            else:
                origin = contents.get(uid)
                field = fields[field_name]
                IFieldDiff(field).copy(origin, canonical)

    def _transfer_back_references(self, content, canonical):
        """Update back references of removed objects
        """
        intids = getUtility(IIntIds)
        canonical_intid = intids.getId(canonical)
        back_references = get_back_references(content)
        # for each back reference...
        for back_reference in back_references:
            from_obj = back_reference['obj']
            attribute = back_reference['attribute']
            value = getattr(from_obj, attribute)
            # we remove relation to content and replace it with a relation to canonical
            if isinstance(value, (tuple, list)):
                for index, item in enumerate(copy(value)):
                    if item.to_path == '/'.join(content.getPhysicalPath()):
                        value.remove(item)
                        # We check if a relation to canon intid not already exists to avoid the following error
                        # ValueError: term values must be unique
                        if not [rel.to_path for rel in value if rel.to_id == canonical_intid]:
                            value.insert(index, RelationValue(canonical_intid))
                        break

                setattr(from_obj, attribute, value)
            else:
                setattr(from_obj, attribute, RelationValue(canonical_intid))

            modified(from_obj)

    def _remove_content_object(self, content, canonical):
        """Move subcontents and references of merged content and remove it
        """
        self._transfer_back_references(content, canonical)
        if len(content.keys()) > 0:
            cb = content.manage_cutObjects(content.keys())
            canonical.manage_pasteObjects(cb)
        IStatusMessage(self.request).add("%s has been removed" %
                                         "/".join(content.getPhysicalPath()))
        api.content.delete(content)

    def __call__(self):
        request = self.request
        values = copy(request.form)
        merge_hp_persons = values.pop('merge-hp-persons', False)
        subcontent_uids = values.pop('subcontent_uids', False)

        extra = values.get('data', None)
        if extra:
            extra = json.loads(extra)
            del values['data']

        contents = {}
        for uid in values.pop('uids'):
            if uid == 'TEMP' and extra:
                contents[uid] = extra
            else:
                content = api.content.get(UID=uid)
                if content is None:
                    BadRequest("Content %s does not exist" % uid)
                contents[uid] = content

        #  get canonical content
        canonical_uid = values.pop('path')  # path contains uid (TODO: rename this)
        canonical = api.content.get(UID=canonical_uid)
        if canonical is None:
            BadRequest("Content %s does not exist" % canonical_uid)

        # update fields
        self._transfer_field_values(values, contents, canonical)

        for (uid, content) in contents.items():
            if content == canonical or uid == 'TEMP':
                continue
            self._remove_content_object(content, canonical)

        modified(canonical)

        # if we merge contacts, merge persons
        next_uids = []
        if merge_hp_persons:
            for content in contents.values():
                if type(content) is dict:  # data field
                    continue
                next_uids.append(IUUID(content.get_person()))
        elif subcontent_uids:
            next_uids = subcontent_uids

        if next_uids:
            request.response.redirect("%s/merge-contacts?%s" % (
                    self.context.absolute_url(),
                    '&'.join(['uids:list=%s' % next_uid
                              for next_uid in next_uids])))
        else:
            request.response.redirect(canonical.absolute_url())
