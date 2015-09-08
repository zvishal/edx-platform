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
        if self.field_name in self.context.get("expand", []):
            self.expanded.bind(self.field_name, self)
            return self.expanded.to_representation(obj)
        else:
            self.collapsed.bind(self.field_name, self)
            return self.collapsed.to_representation(obj)
