"""Fields useful for edX API implementations."""
from rest_framework.serializers import Field


class ExpandableField(Field):
    """Field that can dynamically use a more detailed serializer based on a user-provided "expand" parameter."""
    def __init__(self, **kwargs):
        """Sets up the ExpandableField with the collapsed and expanded versions of the serializer."""
        assert 'collapsed_serializer' in kwargs and 'expanded_serializer' in kwargs
        self.collapsed = kwargs.pop('collapsed_serializer')
        self.expanded = kwargs.pop('expanded_serializer')
        super(ExpandableField, self).__init__(**kwargs)

    def to_representation(self, obj):
        """
        Return a representation of the field that is either expanded or collapsed.
        """
        field = (
            self.expanded
            if self.field_name in self.context.get("expand", [])
            else self.collapsed
        )

        # Avoid double-binding the field, otherwise we'll get
        # an error about the source kwarg being redundant.
        if field.source is None:
            field.bind(self.field_name, self)

        return field.to_representation(obj)
