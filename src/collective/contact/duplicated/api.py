class MergeTool(object):

    def get_field_diff(self, field, contents):
        """Get diff from a list of fields
        @param field: object the zope.schema field to compare
        @param contents: list the list of contents to compare field
        @return None: all fields are empty
                [] all fields are similar
                [*contents] the list of differing fields
        """