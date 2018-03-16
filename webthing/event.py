"""High-level Event base class implementation."""

from .utils import timestamp


class Event:
    """An Event represents an individual event from a thing."""

    def __init__(self, thing, name, description=''):
        """
        Initialize the object.

        thing -- Thing this event belongs to
        name -- name of the event
        description -- description of the event
        """
        self.thing = thing
        self.name = name
        self.description = description
        self.time = timestamp()

    def as_event_description(self):
        """
        Get the event description.

        Returns a dictionary describing the event.
        """
        return {
            self.name: {
                'timestamp': self.time,
            },
        }
