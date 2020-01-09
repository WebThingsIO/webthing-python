"""High-level Subscriber base class implementation."""


class Subscriber:
    """Abstract Subscriber class."""

    def update(self):
        """Receive update from a Thing."""
        raise NotImplementedError

    def update_property(self, property_):
        """
        Receive update from a Thing about an Property.

        :param property_: Property
        """
        raise NotImplementedError

    def update_action(self, action):
        """
        Receive update from a Thing about an Action.

        :param action: Action
        """
        raise NotImplementedError

    def update_event(self, event):
        """
        Receive update from a Thing about an Event.

        :param event: Event
        """
        raise NotImplementedError
