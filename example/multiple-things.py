import random
import threading
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


class ExampleDimmableLight:
    """A dimmable light that logs received commands to stdout."""

    def __init__(self):
        self.thing = Thing('My Lamp', 'dimmableLight', 'A web connected lamp')

        self.thing.add_available_action(
            'fade',
            {'description': 'Fade the lamp to a given level',
             'input': {
                 'type': 'object',
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

        self.thing.add_available_event(
            'overheated',
            {'description':
             'The lamp has exceeded its safe operating temperature',
             'type': 'number',
             'unit': 'celsius'})

        self.thing.add_property(self.get_on_property())
        self.thing.add_property(self.get_level_property())

    def get_on_property(self):
        return Property(self.thing,
                        'on',
                        Value(True, lambda v: print('On-State is now', v)),
                        metadata={
                            'type': 'boolean',
                            'description': 'Whether the lamp is turned on',
                        })

    def get_level_property(self):
        return Property(self.thing,
                        'level',
                        Value(50, lambda l: print('New light level is', l)),
                        metadata={
                            'type': 'number',
                            'description': 'The level of light from 0-100',
                            'minimum': 0,
                            'maximum': 100,
                        })

    def get_thing(self):
        return self.thing


class FakeGpioHumiditySensor:
    """A humidity sensor which updates its measurement every few seconds."""

    def __init__(self):
        self.thing = Thing('My Humidity Sensor',
                           'multiLevelSensor',
                           'A web connected humidity sensor')

        self.thing.add_property(
            Property(self.thing,
                     'on',
                     Value(True),
                     metadata={
                         'type': 'boolean',
                        'description': 'Whether the sensor is on',
                     }))

        self.level = Value(0.0)
        self.thing.add_property(
            Property(self.thing,
                     'level',
                     self.level,
                     metadata={
                         'type': 'number',
                         'description': 'The current humidity in %',
                         'unit': '%',
                     }))

        t = threading.Thread(target=self.update_level)
        t.daemon = True
        t.start()

    def update_level(self):
        while True:
            time.sleep(3)

            # Update the underlying value, which in turn notifies all listeners
            self.level.notify_of_external_update(self.read_from_gpio())

    @staticmethod
    def read_from_gpio():
        """Mimic an actual sensor updating its reading every couple seconds."""
        return 70.0 * random.random() * (-0.5 + random.random())

    def get_thing(self):
        return self.thing


def run_server():
    # Create a thing that represents a dimmable light
    light = ExampleDimmableLight().get_thing()

    # Create a thing that represents a humidity sensor
    sensor = FakeGpioHumiditySensor().get_thing()

    # If adding more than one thing here, be sure to set the `name`
    # parameter to some string, which will be broadcast via mDNS.
    # In the single thing case, the thing's name will be broadcast.
    server = WebThingServer([light, sensor],
                            name='LightAndTempDevice',
                            port=8888)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()


if __name__ == '__main__':
    run_server()
