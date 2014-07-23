# -*- encoding: utf-8 -*-
from App.Common import aq_base
from zope.schema.interfaces import IField, IDate, ICollection,\
    IVocabularyFactory, IBool
from zope.component import adapts
from zope.component import getUtility
from zope.i18n import translate
from zope.interface.declarations import implements
from zope.schema import getFieldsInOrder

from z3c.form.interfaces import NO_VALUE
from z3c.relationfield.interfaces import IRelation

from Products.CMFCore.utils import getToolByName
from plone.app.textfield.interfaces import IRichText
from plone.namedfile.interfaces import INamedField, INamedImageField
from plone.schemaeditor.schema import IChoice
from plone.dexterity.utils import datify
from plone.uuid.interfaces import IUUID

from collective.contact.widget.interfaces import IContactChoice
from collective.contact.duplicated.interfaces import IFieldDiff
from collective.contact.duplicated import _


class BaseFieldDiff(object):
    implements(IFieldDiff)

    def __init__(self, field):
        self.field = field
        self.name = self.field.__name__

    def __repr__(self):
        return "<%s - %s>" % (self.__class__.__name__,
                              self.name)

    def get_value(self, obj):
        return getattr(obj, self.name)

    def render(self, obj):
        value = self.get_value(obj)
        if value in (NO_VALUE, '', None):
            return None
        else:
            return value

    def render_collection_entry(self, obj, value):
        """Render a value element if the field is a sub field of a collection
        """
        return str(value or "")

    def is_different(self, value1, value2):
        return value1 != value2  # @TODO: get a diff

    def copy(self, source, target):
        source_value = getattr(aq_base(source), self.name, None)
        setattr(target, self.name, source_value)


class FieldDiff(BaseFieldDiff):
    adapts(IField)


class FileFieldDiff(BaseFieldDiff):
    adapts(INamedField)

    def render(self, obj):
        """Gets the value to render in excel file from content value
        """
        value = self.get_value(obj)
        return value and value.filename or ""


class ImageFieldDiff(BaseFieldDiff):
    adapts(INamedImageField)

    def render(self, obj):
        """Gets the value to render in excel file from content value
        """
        value = self.get_value(obj)
        if not value:
            return u""

        url = obj.restrictedTraverse('@@images').scale(
                            fieldname=self.name, scale='tile').absolute_url()
        return u"""<img src="%(url)s" title="%(title)s" alt="%(title)s" />""" % {
                        'url': url, 'title': value.filename}


class BooleanFieldDiff(BaseFieldDiff):
    adapts(IBool)

    def render(self, obj):
        value = self.get_value(obj)
        if value in (NO_VALUE, None):
            return u""

        return value and _(u"Yes") or _(u"No")


class DateFieldDiff(BaseFieldDiff):
    adapts(IDate)

    def render(self, obj):
        value = self.get_value(obj)
        datetime = datify(value)
        tlc = obj.unrestrictedTraverse('@@plone').toLocalizedTime
        return translate(tlc(datetime))

    def render_collection_entry(self, obj, value):
        return value.strftime("%Y/%m/%d")


class ChoiceFieldDiff(BaseFieldDiff):
    adapts(IChoice)

    def _get_vocabulary_value(self, obj, value):
        if not value:
            return value

        vocabulary = self.field.vocabulary
        if not vocabulary:
            vocabularyName = self.field.vocabularyName
            if vocabularyName:
                vocabulary = getUtility(IVocabularyFactory, name=vocabularyName)(obj)

        if vocabulary:
            try:
                term = vocabulary.getTermByToken(value)
            except LookupError:
                term = None
        else:
            term = None

        if term:
            title = term.title
            if not title:
                return value
            else:
                return title
        else:
            return value

    def render(self, obj):
        value = self.get_value(obj)
        voc_value = self._get_vocabulary_value(obj, value)
        return voc_value

    def render_collection_entry(self, obj, value):
        voc_value = self._get_vocabulary_value(obj, value)
        return voc_value and translate(voc_value, context=obj.REQUEST) or u""


class CollectionFieldDiff(BaseFieldDiff):
    adapts(ICollection)

    def is_different(self, value1, value2):
        if not value1 and not value2:  # None, [], () are the same
            return False
        else:
            return super(CollectionFieldDiff, self).is_different(value1, value2)

    def render(self, obj):
        """Gets the value to render in excel file from content value
        """
        value = self.get_value(obj)
        if value == []:
            return None

        sub_Diff = IFieldDiff(self.field.value_type)
        return value and u", ".join([sub_Diff.render_collection_entry(obj, v)
                                     for v in value]) or u""


class RichTextFieldDiff(BaseFieldDiff):
    adapts(IRichText)

    def render(self, obj):
        """Gets the value to render in excel file from content value
        """
        value = self.get_value(obj)
        if not value or value == NO_VALUE:
            return ""

        ptransforms = getToolByName(obj, 'portal_transforms')
        text = ptransforms.convert('text_to_html', value.output).getData()
        if len(text) > 50:
            return text[:47] + u"..."


class RelationFieldDiff(BaseFieldDiff):
    adapts(IRelation)

    def is_different(self, value1, value2):
        if value1 is None and value2 is None:
            return False
        elif value1 is None:
            return False
        elif value2 is None:
            return False
        else:
            return IUUID(value1.to_object) != IUUID(value2.to_object)

    def render(self, obj):
        value = self.get_value(obj)
        return self.render_collection_entry(obj, value)

    def render_collection_entry(self, obj, value):
        if not value:
            return u""
        obj = value.to_object
        return """<a href="%s" target="new">%s</a>""" % (obj.absolute_url(),
                                                         obj.Title())


try:
    from collective.z3cform.datagridfield.interfaces import IRow
    HAS_DATAGRIDFIELD = True

    class DictRowFieldDiff(BaseFieldDiff):
        adapts(IRow)

        def render_collection_entry(self, obj, value):
            fields = getFieldsInOrder(self.field.schema)
            field_renderings = []
            for fieldname, field in fields:
                sub_Diff = IFieldDiff(field)
                field_renderings.append(u"%s : %s" % (
                                        sub_Diff.render_header(),
                                        sub_Diff.render_collection_entry(obj,
                                                value.get(fieldname))))

            return u" / ".join([r for r in field_renderings])

        def render(self, obj):
            value = self.get_value(obj)
            return self.render_collection_entry(obj, value)

except:
    HAS_DATAGRIDFIELD = False


class ContactChoiceFieldDiff(RelationFieldDiff):
    adapts(IContactChoice)

    def render_collection_entry(self, obj, value):
        if not value:
            return u""
        obj = value.to_object
        return """<a href="%s" target="new">%s</a>""" % (obj.absolute_url(),
                                                         obj.get_full_title())
