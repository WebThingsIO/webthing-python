"""High-level Property base class implementation."""

from copy import copy


class Property(object):
    """A Property represents an individual state value of a thing."""

    def __init__(self, thing, name, value, metadata=None):
        """
        Initialize the object.

        thing -- the Thing this property belongs to
        name -- name of the property
        value -- Value object to hold the property value
        metadata -- property metadata, i.e. type, description, unit, etc.,
                    as a dict
        """
        self.thing = thing
        self.name = name
        self.value = value
        self.href_prefix = ''
        self.href = '/properties/{}'.format(self.name)
        self.metadata = metadata if metadata is not None else {}

        # Add the property change observer to notify the Thing about a property
        # change.
        self.value.on('update', lambda _: self.thing.property_notify(self))

    def set_href_prefix(self, prefix):
        """
        Set the prefix of any hrefs associated with this property.

        prefix -- the prefix
        """
        self.href_prefix = prefix

    def as_property_description(self):
        """
        Get the property description.

        Returns a dictionary describing the property.
        """
        description = copy(self.metadata)
        description['href'] = self.href_prefix + self.href
        return description

    def get_value(self):
        """
        Get the current property value.

        Returns the value.
        """
        return self.value.get()

    def set_value(self, value):
        """
        Set the current value of the property.

        value -- the value to set
        """
        self.value.set(value)

    def get_name(self):
        """
        Get the name of this property.

        Returns the name.
        """
        return self.name

    def get_thing(self):
        """Get the thing associated with this property."""
        return self.thing
