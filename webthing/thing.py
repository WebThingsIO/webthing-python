"""High-level Thing base class implementation."""


class Thing:
    """A Web Thing."""

    def __init__(self, name, _type='thing', description=''):
        """
        Initialize the object.

        name -- the thing's name
        _type -- the thing's type
        description -- description of the thing
        """
        self.type = _type
        self.name = name
        self.description = description
        self.properties = {}
        self.actions = {}
        self.events = {}

    def as_thing(self, ws_path=None):
        """
        Return the thing state as a Thing Description.

        Returns the state as a dictionary.
        """
        thing = {
            'name': self.name,
            'type': self.type,
            'properties': self.get_property_descriptions(),
            'actions': self.actions,
            'events': self.events,
            'links': {
                'properties': '/thing/{}/properties'.format(self.name),
                'actions': '/thing/{}/actions'.format(self.name),
                'events': '/thing/{}/events'.format(self.name),
            },
        }

        if ws_path is not None:
            thing['links']['websocket'] = \
                '{}/things/{}'.format(ws_path, self.name)

        if self.description:
            thing['description'] = self.description

        return thing

    def get_name(self):
        """
        Get the name of the thing.

        Returns the name as a string.
        """
        return self.name

    def get_type(self):
        """
        Get the type of the thing.

        Returns the type as a string.
        """
        return self.type

    def get_property_descriptions(self):
        """
        Get the thing's properties as a dictionary.

        Returns the properties as a dictionary, i.e. name -> description.
        """
        return {k: v.as_property_description()
                for k, v in self.properties.items()}

    def add_property(self, _property):
        """
        Add a property to this thing.

        _property -- property to add
        """
        self.properties[_property.name] = _property

    def remove_property(self, _property):
        """
        Remove a property from this thing.

        _property -- property to remove
        """
        if _property.name in self.properties:
            del self.properties[_property.name]

    def find_property(self, property_name):
        """
        Find a property by name.

        property_name -- the property to find

        Returns a Property object, if found, else None.
        """
        return self.properties.get(property_name, None)

    def get_property(self, property_name):
        """
        Get a property's value.

        property_name -- the property to get the value of

        Returns the properties value, if found, else None.
        """
        prop = self.find_property(property_name)
        if prop:
            return prop.get_value()

        return None

    def has_property(self, property_name):
        """
        Determine whether or not this thing has a given property.

        property_name -- the property to look for

        Returns a boolean, indicating whether or not the thing has the
        property.
        """
        return property_name in self.properties

    def set_property(self, property_name, value):
        """
        Set a property value.

        property_name -- name of the property to set
        value -- value to set
        """
        prop = self.find_property(property_name)
        if not prop:
            return

        prop.set_value(value)
