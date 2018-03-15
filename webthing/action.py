"""High-level Action base class implementation."""

import datetime


class Action:
    """An Action represents an individual action on a thing."""

    def __init__(self, id_, thing, name, **kwargs):
        """
        Initialize the object.

        id_ ID of this action
        thing -- the Thing this action belongs to
        name -- name of the action
        """
        self.id = id_
        self.thing = thing
        self.name = name
        self.kwargs = kwargs
        self.href = '/actions/{}/{}'.format(self.name, self.id)
        self.status = 'created'
        self.time_requested = \
            datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S+00:00')
        self.time_completed = None
        self.thing.action_notify(self)

    def as_action_description(self):
        """
        Get the action description.

        Returns a dictionary describing the action.
        """
        description = {
            self.name: {
                'href': self.href,
                'timeRequested': self.time_requested,
                'status': self.status,
            },
        }

        if self.time_completed is not None:
            description[self.name]['timeCompleted'] = self.time_completed

        return description

    def start(self):
        """Start performing the action."""
        self.status = 'pending'
        self.thing.action_notify(self)
        self.perform_action()
        self.finish()

    def perform_action(self):
        """Override this with the code necessary to perform the action."""
        pass

    def cancel(self):
        """Override this with the code necessary to cancel the action."""
        pass

    def finish(self):
        """Finish performing the action."""
        self.status = 'completed'
        self.time_completed = \
            datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S+00:00')
        self.thing.action_notify(self)
