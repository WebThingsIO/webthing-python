"""High-level Event base class implementation."""

from .utils import timestamp


class Event:
    """An Event represents an individual event from a thing."""

    def __init__(self, thing, name, data=None):
        """
        Initialize the object.

        thing -- Thing this event belongs to
        name -- name of the event
        data -- data associated with the event
        """
        self.thing = thing
        self.name = name
        self.data = data
        self.time = timestamp()

    def as_event_description(self):
        """
        Get the event description.

        Returns a dictionary describing the event.
        """
        description = {
            self.name: {
                'timestamp': self.time,
            },
        }

        if self.data is not None:
            description[self.name]['data'] = self.data

        return description

    def get_thing(self):
        """Get the thing associated with this event."""
        return self.thing

    def get_name(self):
        """Get the event's name."""
        return self.name

    def get_data(self):
        """Get the event's data."""
        return self.data

    def get_time(self):
        """Get the event's timestamp."""
        return self.time
