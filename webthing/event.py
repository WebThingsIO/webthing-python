"""High-level Event base class implementation."""

import datetime


class Event:
    """An Event represents an individual event from a thing."""

    def __init__(self, thing, name, description=''):
        """
        Initialize the object.

        thing -- the Thing this event belongs to
        name -- name of the event
        description -- description of the event
        """
        self.thing = thing
        self.name = name
        self.description = description
        self.time = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S%z')

    def as_event_description(self):
        """
        Get the event description.

        Returns a dictionary describing the event.
        """
        return {
            'name': self.name,
            'description': self.description,
            'time': self.time,
        }
