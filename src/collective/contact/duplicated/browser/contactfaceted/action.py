from collective.contact.duplicated import _
from collective.contact.facetednav.browser.actions.base import BatchActionBase


class MergeAction(BatchActionBase):

    label = _("Merge duplicated")
    name = "merge"
    klass = "context"
    weight = 800
    multiple_selection = True

    @property
    def onclick(self):
        return "contactduplicated.merge_contacts()"
