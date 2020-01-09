"""High-level Subscriber base class implementation."""

from abc import ABC, abstractmethod


class Subscriber(ABC):
    """
    Abstract Subscriber class.
    """

    @abstractmethod
    def update(self):
        """
        Receive update from a Thing.
        """
        pass

    @abstractmethod
    def update_property(self, property_):
        """
        Receive update from a Thing about an Property.

        :param property_: Property
        """
        pass

    @abstractmethod
    def update_action(self, action):
        """
        Receive update from a Thing about an Action.

        :param action: Action
        """
        pass

    @abstractmethod
    def update_event(self, event):
        """
        Receive update from a Thing about an Event.

        :param event: Event
        """
        pass
