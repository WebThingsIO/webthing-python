"""High-level Thing base class implementation."""

import json
import tornado.websocket


class Thing:
    """A Web Thing."""

    def __init__(self, name='', type_='thing', description=''):
        """
        Initialize the object.

        name -- the thing's name
        type_ -- the thing's type
        description -- description of the thing
        """
        self.type = type_
        self.name = name
        self.description = description
        self.properties = {}
        self.available_actions = {}
        self.available_events = {}
        self.actions = []
        self.events = []
        self.subscribers = set()

    def as_thing_description(self, ws_path=None):
        """
        Return the thing state as a Thing Description.

        Returns the state as a dictionary.
        """
        thing = {
            'name': self.name,
            'href': '/',
            'type': self.type,
            'properties': self.get_property_descriptions(),
            'actions': {
                name: {'description': action['description']}
                for name, action in self.available_actions.items()
            },
            'events': {
                name: {'description': event['description']}
                for name, event in self.available_events.items()
            },
            'links': {
                'properties': '/properties',
                'actions': '/actions',
                'events': '/events',
            },
        }

        if ws_path is not None:
            thing['links']['websocket'] = ws_path

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

    def add_property(self, property_):
        """
        Add a property to this thing.

        property_ -- property to add
        """
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

    def add_event(self, event):
        """
        Add a new event and notify subscribers.

        event -- the event that occurred
        """
        self.events.append(event)
        self.event_notify(event)

    def add_event_description(self, name, description):
        """
        Add an event description.

        name -- name of the event
        description -- event description
        """
        self.available_events[name] = {
            'description': description,
            'subscribers': set(),
        }

    def perform_action(self, action_name, **kwargs):
        """
        Perform an action on the thing.

        action_name -- name of the action
        """
        if action_name not in self.available_actions:
            return

        action = self.available_actions[action_name]['class'](self, **kwargs)
        self.actions.append(action)

    def add_action_description(self, name, description, cls):
        """
        Add an action description.

        name -- name of the action
        description -- description of the action
        cls -- class to instantiate for this action
        """
        self.available_actions[name] = {
            'description': description,
            'class': cls,
        }

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
        for subscriber in self.subscribers:
            try:
                subscriber.write_message(json.dumps({
                    'messageType': 'propertyStatus',
                    'data': {
                        property_.name: property_.get_value(),
                    }
                }))
            except tornado.websocket.WebSocketClosedError:
                pass

    def action_notify(self, action):
        """
        Notify all subscribers of an action status change.

        action -- the action whose status changed
        """
        for subscriber in self.subscribers:
            try:
                subscriber.write_message(json.dumps({
                    'messageType': 'actionStatus',
                    'data': {
                        action.name: {
                            'href': action.href,
                            'status': action.status,
                        },
                    },
                }))
            except tornado.websocket.WebSocketClosedError:
                pass

    def event_notify(self, event):
        """
        Notify all subscribers of an event.

        event -- the event that occurred
        """
        if event.name not in self.available_events:
            return

        for subscriber in self.available_events[event.name]['subscribers']:
            try:
                subscriber.write_message(json.dumps({
                    'messageType': 'event',
                    'data': {
                        event.name: {
                            'timestamp': event.time,
                        },
                    },
                }))
            except tornado.websocket.WebSocketClosedError:
                pass
