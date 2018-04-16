import time
import uuid

from webthing import Action, Event, Property, Thing, Value, WebThingServer


class OverheatedEvent(Event):

    def __init__(self, thing, data):
        Event.__init__(self, thing, 'overheated', data=data)


class FadeAction(Action):

    def __init__(self, thing, input_):
        Action.__init__(self, uuid.uuid4().hex, thing, 'fade', input_=input_)

    def perform_action(self):
        time.sleep(self.input['duration'] / 1000)
        self.thing.set_property('level', self.input['level'])
        self.thing.add_event(OverheatedEvent(self.thing, 102))


def make_thing():
    thing = Thing(name='My Lamp', description='A web connected lamp')

    def noop(_):
        pass

    thing.add_property(
        Property(thing,
                 'on',
                 Value(True, noop),
                 metadata={
                     'type': 'boolean',
                     'description': 'Whether the lamp is turned on',
                 }))
    thing.add_property(
        Property(thing,
                 'level',
                 Value(50, noop),
                 metadata={
                     'type': 'number',
                     'description': 'The level of light from 0-100',
                     'minimum': 0,
                     'maximum': 100,
                 }))

    thing.add_available_action(
        'fade',
        {'description': 'Fade the lamp to a given level',
         'input': {
             'type': 'object',
             'required': [
                 'level',
                 'duration',
             ],
             'properties': {
                 'level': {
                     'type': 'number',
                     'minimum': 0,
                     'maximum': 100,
                 },
                 'duration': {
                     'type': 'number',
                     'unit': 'milliseconds',
                 },
             },
         }},
        FadeAction)

    thing.add_available_event(
        'overheated',
        {'description': 'The lamp has exceeded its safe operating temperature',
         'type': 'number',
         'unit': 'celsius'})

    return thing


def run_server():
    thing = make_thing()

    # If adding more than one thing here, be sure to set the `name`
    # parameter to some string, which will be broadcast via mDNS.
    # In the single thing case, the thing's name will be broadcast.
    server = WebThingServer([thing], port=8888)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()


if __name__ == '__main__':
    run_server()
