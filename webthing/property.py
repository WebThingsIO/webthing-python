"""High-level Property base class implementation."""


class Property:
    """A Property represents an individual state value of a thing."""

    def __init__(self, thing, name, metadata=None, value=None):
        """
        Initialize the object.

        thing -- the Thing this property belongs to
        name -- name of the property
        metadata -- property metadata, i.e. type, description, unit, etc.,
                    as a dict
        value -- initial value of property
        """
        self.thing = thing
        self.name = name
        self.value = value
        self.metadata = metadata if metadata is not None else {}
        self.metadata['href'] = '/properties/{}'.format(self.name)

    def as_property_description(self):
        """
        Get the property description.

        Returns a dictionary describing the property.
        """
        return self.metadata

    def set_cached_value(self, value):
        """
        Set the cached value of the property, making adjustments as necessary.

        value -- the value to set

        Returns the value that was set.
        """
        if 'type' in self.metadata and \
                self.metadata['type'] == 'boolean':
            self.value = bool(value)
        else:
            self.value = value

        self.thing.property_notify(self)
        return self.value

    def get_value(self):
        """
        Get the current property value.

        Returns the value.
        """
        return self.value

    def set_value(self, value):
        """
        Set the current value of the property.

        value -- the value to set
        """
        self.set_cached_value(value)

    def get_name(self):
        """
        Get the name of this property.

        Returns the name.
        """
        return self.name

    def get_thing(self):
        """Get the thing associated with this property."""
        return self.thing
