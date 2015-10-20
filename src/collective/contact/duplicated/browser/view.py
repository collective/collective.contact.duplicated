from copy import copy

from zope.intid.interfaces import IIntIds
from zExceptions import NotFound
from zope.component import getUtility
from zope.lifecycleevent import modified
from z3c.relationfield.relation import RelationValue

from Products.Five.browser import BrowserView
from plone import api
from plone.uuid.interfaces import IUUID

from collective.contact.core.content.held_position import IHeldPosition
from collective.contact.duplicated.interfaces import IFieldDiff
from collective.contact.duplicated.api import get_back_references,\
    get_fieldsets, get_fields
from Products.statusmessages.interfaces import IStatusMessage


class Compare(BrowserView):

    def get_contents(self):
        uids = self.request['uids']
        contents = api.portal.get_tool('portal_catalog')(UID=uids)
        if len(contents) != len(uids):
            raise NotFound

        # one content type
        assert len(set([b.portal_type for b in contents])) == 1
        content_objs = [c.getObject() for c in contents]
        return [{'obj': obj,
                 'uid': IUUID(obj),
                 'path': '/'.join(obj.getPhysicalPath()),
                 'back_references': get_back_references(obj),
                 'subcontents': obj.values()} for obj in content_objs]

    def update(self):
        self.contents = self.get_contents()
        first = self.contents[0]['obj']
        self.portal_type = first.portal_type
        self.fieldsets = get_fieldsets(self.portal_type)

        # check if this is contacts from different persons,
        # then we can also merge the persons
        self.merge_hp_persons = False
        if IHeldPosition.providedBy(first):
            person_uids = [IUUID(hp['obj'].get_person()) for hp in self.contents]
            if len(set(person_uids)) > 1:
                self.merge_hp_persons = True
                self.merge_person_url = "%s/merge-contacts?%s" % (
                    self.context.absolute_url(),
                    '&'.join(['uids:list=%s' % uid for uid in person_uids]))

    def diff(self, field):
        field_diff = IFieldDiff(field)
        values = [getattr(c['obj'], field.__name__) for c in self.contents]
        #  check if at least two values differ
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
            if field_name == '_authenticator':
                continue
            if uid == canonical_uid:
                continue
            elif uid == 'empty':
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
        for back_reference in back_references:
            from_obj = back_reference['obj']
            attribute = back_reference['attribute']
            value = getattr(from_obj, attribute)
            if isinstance(value, (tuple, list)):
                for index, v in enumerate(copy(value)):
                    if v.to_object == content:
                        value.remove(v)
                        value.insert(index, RelationValue(canonical_intid))

                    setattr(from_obj, attribute, value)
            else:
                setattr(from_obj, attribute, RelationValue(canonical_intid))

            modified(from_obj)

    def _remove_content_object(self, content, canonical):
        """Move subcontents and references of merged content and remove it
        """
        self._transfer_back_references(content, canonical)
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
        contents = dict([(uid, api.content.get(UID=uid))
                         for uid in values.pop('uids')])

        #  get canonical content
        canonical_uid = values.pop('path')
        canonical = api.content.get(UID=canonical_uid)

        # update fields
        self._transfer_field_values(values, contents, canonical)

        for content in contents.values():
            if content == canonical:
                continue
            self._remove_content_object(content, canonical)

        modified(canonical)

        # if we merge contacts, merge persons
        next_uids = []
        if merge_hp_persons:
            next_uids = [IUUID(content.get_person())
                         for content in contents.values()]
        elif subcontent_uids:
            next_uids = subcontent_uids

        if next_uids:
            request.response.redirect("%s/merge-contacts?%s" % (
                    self.context.absolute_url(),
                    '&'.join(['uids:list=%s' % next_uid
                              for next_uid in next_uids])))
        else:
            request.response.redirect(canonical.absolute_url())
