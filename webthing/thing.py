"""High-level Thing base class implementation."""

from jsonschema import validate
from jsonschema.exceptions import ValidationError


class Thing:
    """A Web Thing."""

    def __init__(self, id_, title, type_=[], description=''):
        """
        Initialize the object.

        id_ -- the thing's unique ID - must be a URI
        title -- the thing's title
        type_ -- the thing's type(s)
        description -- description of the thing
        """
        if not isinstance(type_, list):
            type_ = [type_]

        self.id = id_
        self.context = 'https://webthings.io/schemas'
        self.type = type_
        self.title = title
        self.description = description
        self.properties = {}
        self.available_actions = {}
        self.available_events = {}
        self.actions = {}
        self.events = []
        self.subscribers = set()
        self.href_prefix = ''
        self.ui_href = None

    def as_thing_description(self):
        """
        Return the thing state as a Thing Description.

        Returns the state as a dictionary.
        """
        thing = {
            'id': self.id,
            'title': self.title,
            '@context': self.context,
            'properties': self.get_property_descriptions(),
            'actions': {},
            'events': {},
            'links': [
                {
                    'rel': 'properties',
                    'href': '{}/properties'.format(self.href_prefix),
                },
                {
                    'rel': 'actions',
                    'href': '{}/actions'.format(self.href_prefix),
                },
                {
                    'rel': 'events',
                    'href': '{}/events'.format(self.href_prefix),
                },
            ],
        }

        for name, action in self.available_actions.items():
            thing['actions'][name] = action['metadata']
            thing['actions'][name]['links'] = [
                {
                    'rel': 'action',
                    'href': '{}/actions/{}'.format(self.href_prefix, name),
                },
            ]

        for name, event in self.available_events.items():
            thing['events'][name] = event['metadata']
            thing['events'][name]['links'] = [
                {
                    'rel': 'event',
                    'href': '{}/events/{}'.format(self.href_prefix, name),
                },
            ]

        if self.ui_href is not None:
            thing['links'].append({
                'rel': 'alternate',
                'mediaType': 'text/html',
                'href': self.ui_href,
            })

        if self.description:
            thing['description'] = self.description

        if self.type:
            thing['@type'] = self.type

        return thing

    def get_href(self):
        """Get this thing's href."""
        if self.href_prefix:
            return self.href_prefix

        return '/'

    def get_ui_href(self):
        """Get the UI href."""
        return self.ui_href

    def set_href_prefix(self, prefix):
        """
        Set the prefix of any hrefs associated with this thing.

        prefix -- the prefix
        """
        self.href_prefix = prefix

        for property_ in self.properties.values():
            property_.set_href_prefix(prefix)

        for action_name in self.actions.keys():
            for action in self.actions[action_name]:
                action.set_href_prefix(prefix)

    def set_ui_href(self, href):
        """
        Set the href of this thing's custom UI.

        href -- the href
        """
        self.ui_href = href

    def get_id(self):
        """
        Get the ID of the thing.

        Returns the ID as a string.
        """
        return self.id

    def get_title(self):
        """
        Get the title of the thing.

        Returns the title as a string.
        """
        return self.title

    def get_context(self):
        """
        Get the type context of the thing.

        Returns the context as a string.
        """
        return self.context

    def get_type(self):
        """
        Get the type(s) of the thing.

        Returns the list of types.
        """
        return self.type

    def get_description(self):
        """
        Get the description of the thing.

        Returns the description as a string.
        """
        return self.description

    def get_property_descriptions(self):
        """
        Get the thing's properties as a dictionary.

        Returns the properties as a dictionary, i.e. name -> description.
        """
        return {k: v.as_property_description()
                for k, v in self.properties.items()}

    def get_action_descriptions(self, action_name=None):
        """
        Get the thing's actions as an array.

        action_name -- Optional action name to get descriptions for

        Returns the action descriptions.
        """
        descriptions = []

        if action_name is None:
            for name in self.actions:
                for action in self.actions[name]:
                    descriptions.append(action.as_action_description())
        elif action_name in self.actions:
            for action in self.actions[action_name]:
                descriptions.append(action.as_action_description())

        return descriptions

    def get_event_descriptions(self, event_name=None):
        """
        Get the thing's events as an array.

        event_name -- Optional event name to get descriptions for

        Returns the event descriptions.
        """
        if event_name is None:
            return [e.as_event_description() for e in self.events]
        else:
            return [e.as_event_description()
                    for e in self.events if e.get_name() == event_name]

    def add_property(self, property_):
        """
        Add a property to this thing.

        property_ -- property to add
        """
        property_.set_href_prefix(self.href_prefix)
        self.properties[property_.name] = property_

    def remove_property(self, property_):
        """
        Remove a property from this thing.

        property_ -- property to remove
        """
        if property_.name in self.properties:
            del self.properties[property_.name]

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

    def get_properties(self):
        """
        Get a mapping of all properties and their values.

        Returns a dictionary of property_name -> value.
        """
        return {prop.get_name(): prop.get_value()
                for prop in self.properties.values()}

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

    def get_action(self, action_name, action_id):
        """
        Get an action.

        action_name -- name of the action
        action_id -- ID of the action

        Returns the requested action if found, else None.
        """
        if action_name not in self.actions:
            return None

        for action in self.actions[action_name]:
            if action.id == action_id:
                return action

        return None

    def add_event(self, event):
        """
        Add a new event and notify subscribers.

        event -- the event that occurred
        """
        self.events.append(event)
        self.event_notify(event)

    def add_available_event(self, name, metadata):
        """
        Add an available event.

        name -- name of the event
        metadata -- event metadata, i.e. type, description, etc., as a dict
        """
        if metadata is None:
            metadata = {}

        self.available_events[name] = {
            'metadata': metadata,
            'subscribers': set(),
        }

    def perform_action(self, action_name, input_=None):
        """
        Perform an action on the thing.

        action_name -- name of the action
        input_ -- any action inputs

        Returns the action that was created.
        """
        if action_name not in self.available_actions:
            return None

        action_type = self.available_actions[action_name]

        if 'input' in action_type['metadata']:
            try:
                validate(input_, action_type['metadata']['input'])
            except ValidationError:
                return None

        action = action_type['class'](self, input_=input_)
        action.set_href_prefix(self.href_prefix)
        self.action_notify(action)
        self.actions[action_name].append(action)
        return action

    def remove_action(self, action_name, action_id):
        """
        Remove an existing action.

        action_name -- name of the action
        action_id -- ID of the action

        Returns a boolean indicating the presence of the action.
        """
        action = self.get_action(action_name, action_id)
        if action is None:
            return False

        action.cancel()
        self.actions[action_name].remove(action)
        return True

    def add_available_action(self, name, metadata, cls):
        """
        Add an available action.

        name -- name of the action
        metadata -- action metadata, i.e. type, description, etc., as a dict
        cls -- class to instantiate for this action
        """
        if metadata is None:
            metadata = {}

        self.available_actions[name] = {
            'metadata': metadata,
            'class': cls,
        }
        self.actions[name] = []

    def add_subscriber(self, subscriber):
        """
        Add a new websocket subscriber.

        :param subscriber: Subscriber
        """
        self.subscribers.add(subscriber)

    def remove_subscriber(self, subscriber):
        """
        Remove a websocket subscriber.

        :param subscriber: Subscriber
        """
        if subscriber in self.subscribers:
            self.subscribers.remove(subscriber)

        for name in self.available_events:
            self.remove_event_subscriber(name, subscriber)

    def add_event_subscriber(self, name, subscriber):
        """
        Add a new websocket subscriber to an event.

        :param name: Name of the event
        :param subscriber: Subscriber
        """
        if name in self.available_events:
            self.available_events[name]['subscribers'].add(subscriber)

    def remove_event_subscriber(self, name, subscriber):
        """
        Remove a websocket subscriber from an event.

        :param name: Name of the event
        :param subscriber: Subscriber
        """
        if name in self.available_events and \
                subscriber in self.available_events[name]['subscribers']:
            self.available_events[name]['subscribers'].remove(subscriber)

    def property_notify(self, property_):
        """
        Notify all subscribers of a property change.

        :param property_: the property that changed
        """
        for subscriber in list(self.subscribers):
            subscriber.update_property(property_)

    def action_notify(self, action):
        """
        Notify all subscribers of an action status change.

        :param action: The action whose status changed
        """
        for subscriber in list(self.subscribers):
            subscriber.update_action(action)

    def event_notify(self, event):
        """
        Notify all subscribers of an event.

        :param event: The event that occurred
        """
        if event.name not in self.available_events:
            return

        for subscriber in self.available_events[event.name]['subscribers']:
            subscriber.update_event(event)
