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

from collective.contact.widget.interfaces import IContactChoice
from collective.contact.duplicated.interfaces import IFieldRenderer
from collective.contact.duplicated import _


class BaseFieldRenderer(object):
    implements(IFieldRenderer)

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


class FieldRenderer(BaseFieldRenderer):
    adapts(IField)


class BaseFieldValueCopy(object):

    def __init__(self, field):
        self.field = field
        self.name = self.field.__name__

    def __repr__(self):
        return "<%s - %s>" % (self.__class__.__name__,
                              self.name)

    def transfer(self, source, target):
        source_value = getattr(aq_base(source), self.name, None)
        setattr(target, self.name, source_value)


class FieldValueCopy(BaseFieldValueCopy):
    adapts(IField)


class FileFieldRenderer(BaseFieldRenderer):
    adapts(INamedField)

    def render(self, obj):
        """Gets the value to render in excel file from content value
        """
        value = self.get_value(obj)
        return value and value.filename or ""


class ImageFieldRenderer(BaseFieldRenderer):
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


class BooleanFieldRenderer(BaseFieldRenderer):
    adapts(IBool)

    def render(self, obj):
        value = self.get_value(obj)
        return value and _(u"Yes") or _(u"No")


class DateFieldRenderer(BaseFieldRenderer):
    adapts(IDate)

    def render(self, obj):
        value = self.get_value(obj)
        datetime = datify(value)
        tlc = obj.unrestrictedTraverse('@@plone').toLocalizedTime
        return translate(tlc(datetime))

    def render_collection_entry(self, obj, value):
        return value.strftime("%Y/%m/%d")


class ChoiceFieldRenderer(BaseFieldRenderer):
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


class CollectionFieldRenderer(BaseFieldRenderer):
    adapts(ICollection)

    def render(self, obj):
        """Gets the value to render in excel file from content value
        """
        value = self.get_value(obj)
        if value == []:
            return None

        sub_renderer = IFieldRenderer(self.field.value_type)
        return value and u", ".join([sub_renderer.render_collection_entry(obj, v)
                                     for v in value]) or u""


class RichTextFieldRenderer(BaseFieldRenderer):
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


class RelationFieldRenderer(BaseFieldRenderer):
    adapts(IRelation)

    def render(self, obj):
        value = self.get_value(obj)
        return self.render_collection_entry(obj, value)

    def render_collection_entry(self, obj, value):
        return value and value.to_object and value.to_object.Title() or u""


try:
    from collective.z3cform.datagridfield.interfaces import IRow
    HAS_DATAGRIDFIELD = True

    class DictRowFieldRenderer(BaseFieldRenderer):
        adapts(IRow)

        def render_collection_entry(self, obj, value):
            fields = getFieldsInOrder(self.field.schema)
            field_renderings = []
            for fieldname, field in fields:
                sub_renderer = IFieldRenderer(field)
                field_renderings.append(u"%s : %s" % (
                                        sub_renderer.render_header(),
                                        sub_renderer.render_collection_entry(obj,
                                                value.get(fieldname))))

            return u" / ".join([r for r in field_renderings])

        def render(self, obj):
            value = self.get_value(obj)
            return self.render_collection_entry(obj, value)

except:
    HAS_DATAGRIDFIELD = False


class ContactChoiceFieldRenderer(BaseFieldRenderer):
    adapts(IContactChoice)

    def render(self, obj):
        value = self.get_value(obj)
        return self.render_collection_entry(obj, value)

    def render_collection_entry(self, obj, value):
        return value and value.to_object and value.to_object.get_full_title() or u""
