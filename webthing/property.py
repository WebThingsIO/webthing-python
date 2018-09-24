"""High-level Property base class implementation."""

from copy import copy

from .errors import PropertyError


class Property:
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

    def validate_value(self, value):
        """
        Validate new property value before setting it.

        value -- New value
        """
        if 'type' in self.metadata:
            t = self.metadata['type']

            if t == 'null':
                if t is not None:
                    raise PropertyError('Value must be null')
            elif t == 'boolean':
                if type(value) is not bool:
                    raise PropertyError('Value must be a boolean')
            elif t == 'object':
                if type(value) is not dict:
                    raise PropertyError('Value must be an object')
            elif t == 'array':
                if type(value) is not list:
                    raise PropertyError('Value must be an array')
            elif t == 'number':
                if type(value) not in [float, int]:
                    raise PropertyError('Value must be a number')
            elif t == 'integer':
                if type(value) is not int:
                    raise PropertyError('Value must be an integer')
            elif t == 'string':
                if type(value) is not str:
                    raise PropertyError('Value must be a string')

        if 'readOnly' in self.metadata and self.metadata['readOnly']:
            raise PropertyError('Read-only property')

        if 'minimum' in self.metadata and value < self.metadata['minimum']:
            raise PropertyError('Value less than minimum: {}'
                                .format(self.metadata['minimum']))

        if 'maximum' in self.metadata and value > self.metadata['maximum']:
            raise PropertyError('Value greater than maximum: {}'
                                .format(self.metadata['maximum']))

        if 'enum' in self.metadata and len(self.metadata['enum']) > 0 and \
                value not in self.metadata['enum']:
            raise PropertyError('Invalid enum value')

    def as_property_description(self):
        """
        Get the property description.

        Returns a dictionary describing the property.
        """
        description = copy(self.metadata)
        description['href'] = self.href_prefix + self.href
        return description

    def set_href_prefix(self, prefix):
        """
        Set the prefix of any hrefs associated with this property.

        prefix -- the prefix
        """
        self.href_prefix = prefix

    def get_href(self):
        """
        Get the href of this property.

        Returns the href.
        """
        return self.href_prefix + self.href

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
        self.validate_value(value)
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

    def get_metadata(self):
        """Get the metadata associated with this property."""
        return self.metadata
