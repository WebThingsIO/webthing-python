"""High-level Property base class implementation."""

from copy import deepcopy
from jsonschema import validate
from jsonschema.exceptions import ValidationError

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
        if 'readOnly' in self.metadata and self.metadata['readOnly']:
            raise PropertyError('Read-only property')

        try:
            validate(value, self.metadata)
        except ValidationError:
            raise PropertyError('Invalid property value')

    def as_property_description(self):
        """
        Get the property description.

        Returns a dictionary describing the property.
        """
        description = deepcopy(self.metadata)

        if 'links' not in description:
            description['links'] = []

        description['links'].append(
            {
                'rel': 'property',
                'href': self.href_prefix + self.href,
            }
        )
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
