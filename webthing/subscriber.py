from abc import ABC, abstractmethod

from .action import Action
from .event import Event
from .property import Property


class Subscriber(ABC):

    @abstractmethod
    def update(self) -> None:
        """
        Receive update from a Thing.
        """
        pass

    @abstractmethod
    def update_property(self, property_: Property) -> None:
        """
        Receive update from a Thing about an Property

        :param property_: Property
        """
        pass

    @abstractmethod
    def update_action(self, action: Action) -> None:
        """
        Receive update from a Thing about an Action

        :param action: Action
        """
        pass

    @abstractmethod
    def update_event(self, event: Event) -> None:
        """
        Receive update from a Thing about an Event

        :param event: Event
        """
        pass
