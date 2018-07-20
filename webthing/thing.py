"""High-level Thing base class implementation."""

from jsonschema import validate
from jsonschema.exceptions import ValidationError
import json
import tornado.websocket


class Thing:
    """A Web Thing."""

    def __init__(self, name, type_=[], description=''):
        """
        Initialize the object.

        name -- the thing's name
        type_ -- the thing's type(s)
        description -- description of the thing
        """
        if not isinstance(type_, list):
            type_ = [type_]

        self.context = 'https://iot.mozilla.org/schemas'
        self.type = type_
        self.name = name
        self.description = description
        self.properties = {}
        self.available_actions = {}
        self.available_events = {}
        self.actions = {}
        self.events = []
        self.subscribers = set()
        self.href_prefix = ''
        self.ws_href = None
        self.ui_href = None

    def as_thing_description(self):
        """
        Return the thing state as a Thing Description.

        Returns the state as a dictionary.
        """
        thing = {
            'name': self.name,
            'href': self.href_prefix if self.href_prefix else '/',
            '@context': self.context,
            '@type': self.type,
            'properties': self.get_property_descriptions(),
            'actions': {
                name: action['metadata']
                for name, action in self.available_actions.items()
            },
            'events': {
                name: event['metadata']
                for name, event in self.available_events.items()
            },
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

        if self.ws_href is not None:
            thing['links'].append({
                'rel': 'alternate',
                'href': self.ws_href,
            })

        if self.ui_href is not None:
            thing['links'].append({
                'rel': 'alternate',
                'mediaType': 'text/html',
                'href': self.ui_href,
            })

        if self.description:
            thing['description'] = self.description

        return thing

    def get_href(self):
        """Get this thing's href."""
        if self.href_prefix:
            return self.href_prefix

        return '/'

    def get_ws_href(self):
        """Get the websocket href."""
        return self.ws_href

    def get_ui_href(self):
        """Get the UI href."""
        return self.ui_href

    def set_href_prefix(self, prefix):
        """
        Set the prefix of any hrefs associated with this thing.

        prefix -- the prefix
        """
        self.href_prefix = prefix

        for action in self.available_actions.values():
            action['metadata']['href'] = prefix + action['metadata']['href']

        for event in self.available_events.values():
            event['metadata']['href'] = prefix + event['metadata']['href']

        for property_ in self.properties.values():
            property_.set_href_prefix(prefix)

        for action_name in self.actions.keys():
            for action in self.actions[action_name]:
                action.set_href_prefix(prefix)

    def set_ws_href(self, href):
        """
        Set the href of this thing's websocket.

        href -- the href
        """
        self.ws_href = href

    def set_ui_href(self, href):
        """
        Set the href of this thing's custom UI.

        href -- the href
        """
        self.ui_href = href

    def get_name(self):
        """
        Get the name of the thing.

        Returns the name as a string.
        """
        return self.name

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

        metadata['href'] = '/events/{}'.format(name)

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

        metadata['href'] = '/actions/{}'.format(name)

        self.available_actions[name] = {
            'metadata': metadata,
            'class': cls,
        }
        self.actions[name] = []

    def add_subscriber(self, ws):
        """
        Add a new websocket subscriber.

        ws -- the websocket
        """
        self.subscribers.add(ws)

    def remove_subscriber(self, ws):
        """
        Remove a websocket subscriber.

        ws -- the websocket
        """
        if ws in self.subscribers:
            self.subscribers.remove(ws)

        for name in self.available_events:
            self.remove_event_subscriber(name, ws)

    def add_event_subscriber(self, name, ws):
        """
        Add a new websocket subscriber to an event.

        name -- name of the event
        ws -- the websocket
        """
        if name in self.available_events:
            self.available_events[name]['subscribers'].add(ws)

    def remove_event_subscriber(self, name, ws):
        """
        Remove a websocket subscriber from an event.

        name -- name of the event
        ws -- the websocket
        """
        if name in self.available_events and \
                ws in self.available_events[name]['subscribers']:
            self.available_events[name]['subscribers'].remove(ws)

    def property_notify(self, property_):
        """
        Notify all subscribers of a property change.

        property_ -- the property that changed
        """
        message = json.dumps({
            'messageType': 'propertyStatus',
            'data': {
                property_.name: property_.get_value(),
            }
        })

        for subscriber in self.subscribers:
            try:
                subscriber.write_message(message)
            except tornado.websocket.WebSocketClosedError:
                pass

    def action_notify(self, action):
        """
        Notify all subscribers of an action status change.

        action -- the action whose status changed
        """
        message = json.dumps({
            'messageType': 'actionStatus',
            'data': action.as_action_description(),
        })

        for subscriber in self.subscribers:
            try:
                subscriber.write_message(message)
            except tornado.websocket.WebSocketClosedError:
                pass

    def event_notify(self, event):
        """
        Notify all subscribers of an event.

        event -- the event that occurred
        """
        if event.name not in self.available_events:
            return

        message = json.dumps({
            'messageType': 'event',
            'data': event.as_event_description(),
        })

        for subscriber in self.available_events[event.name]['subscribers']:
            try:
                subscriber.write_message(message)
            except tornado.websocket.WebSocketClosedError:
                pass
