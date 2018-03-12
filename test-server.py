import time
import uuid

from webthing import Action, Event, Property, Thing, WebThingServer


class RebootEvent(Event):

    def __init__(self, thing):
        Event.__init__(self,
                       thing,
                       'reboot',
                       description='Going down for reboot')


class RebootAction(Action):

    def __init__(self, thing, **kwargs):
        Action.__init__(self, uuid.uuid4().hex, thing, 'reboot', **kwargs)

    def perform_action(self):
        self.thing.add_event(RebootEvent(self.thing))
        time.sleep(1)


def run_server():
    thing = Thing(name='WoT Pi', description='A WoT-connected Raspberry Pi')

    thing.add_property(
        Property(thing,
                 'temperature',
                 {'type': 'number',
                  'unit': 'celsius',
                  'description': 'An ambient temperature sensor'}))
    thing.add_property(
        Property(thing,
                 'humidity',
                 {'type': 'number',
                  'unit': 'percent'}))
    thing.add_property(
        Property(thing,
                 'led',
                 {'type': 'boolean',
                  'description': 'A red LED'}))

    thing.add_action_description('reboot', 'Reboot the device', RebootAction)
    thing.add_event_description('reboot', 'Going down for reboot')

    server = WebThingServer(thing, port=8888)
    server.start()


if __name__ == '__main__':
    run_server()
