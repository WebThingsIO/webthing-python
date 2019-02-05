from __future__ import division, print_function
from webthing import (Action, Event, MultipleThings, Property, Thing, Value,
                      WebThingServer)
import logging
import random
import time
import tornado.ioloop
import uuid


class OverheatedEvent(Event):

    def __init__(self, thing, data):
        Event.__init__(self, thing, 'overheated', data=data)


class FadeAction(Action):

    def __init__(self, thing, input_):
        Action.__init__(self, uuid.uuid4().hex, thing, 'fade', input_=input_)

    def perform_action(self):
        time.sleep(self.input['duration'] / 1000)
        self.thing.set_property('brightness', self.input['brightness'])
        self.thing.add_event(OverheatedEvent(self.thing, 102))


class ExampleDimmableLight(Thing):
    """A dimmable light that logs received commands to stdout."""

    def __init__(self):
        Thing.__init__(self,
                       'My Lamp',
                       ['OnOffSwitch', 'Light'],
                       'A web connected lamp')

        self.add_property(
            Property(self,
                     'on',
                     Value(True, lambda v: print('On-State is now', v)),
                     metadata={
                         '@type': 'OnOffProperty',
                         'title': 'On/Off',
                         'type': 'boolean',
                         'description': 'Whether the lamp is turned on',
                     }))

        self.add_property(
            Property(self,
                     'brightness',
                     Value(50, lambda v: print('Brightness is now', v)),
                     metadata={
                         '@type': 'BrightnessProperty',
                         'title': 'Brightness',
                         'type': 'integer',
                         'description': 'The level of light from 0-100',
                         'minimum': 0,
                         'maximum': 100,
                         'unit': 'percent',
                     }))

        self.add_available_action(
            'fade',
            {
                'title': 'Fade',
                'description': 'Fade the lamp to a given level',
                'input': {
                    'type': 'object',
                    'required': [
                        'brightness',
                        'duration',
                    ],
                    'properties': {
                        'brightness': {
                            'type': 'integer',
                            'minimum': 0,
                            'maximum': 100,
                            'unit': 'percent',
                        },
                        'duration': {
                            'type': 'integer',
                            'minimum': 1,
                            'unit': 'milliseconds',
                        },
                    },
                },
            },
            FadeAction)

        self.add_available_event(
            'overheated',
            {
                'description':
                'The lamp has exceeded its safe operating temperature',
                'type': 'number',
                'unit': 'degree celsius',
            })


class FakeGpioHumiditySensor(Thing):
    """A humidity sensor which updates its measurement every few seconds."""

    def __init__(self):
        Thing.__init__(self,
                       'My Humidity Sensor',
                       ['MultiLevelSensor'],
                       'A web connected humidity sensor')

        self.level = Value(0.0)
        self.add_property(
            Property(self,
                     'level',
                     self.level,
                     metadata={
                         '@type': 'LevelProperty',
                         'title': 'Humidity',
                         'type': 'number',
                         'description': 'The current humidity in %',
                         'minimum': 0,
                         'maximum': 100,
                         'unit': 'percent',
                         'readOnly': True,
                     }))

        logging.debug('starting the sensor update looping task')
        self.timer = tornado.ioloop.PeriodicCallback(
            self.update_level,
            3000
        )
        self.timer.start()

    def update_level(self):
        new_level = self.read_from_gpio()
        logging.debug('setting new humidity level: %s', new_level)
        self.level.notify_of_external_update(new_level)

    def cancel_update_level_task(self):
        self.sensor_update_task.cancel()
        get_event_loop().run_until_complete(self.sensor_update_task)

    @staticmethod
    def read_from_gpio():
        """Mimic an actual sensor updating its reading every couple seconds."""
        return abs(70.0 * random.random() * (-0.5 + random.random()))


def run_server():
    # Create a thing that represents a dimmable light
    light = ExampleDimmableLight()

    # Create a thing that represents a humidity sensor
    sensor = FakeGpioHumiditySensor()

    # If adding more than one thing, use MultipleThings() with a name.
    # In the single thing case, the thing's name will be broadcast.
    server = WebThingServer(MultipleThings([light, sensor],
                                           'LightAndTempDevice'),
                            port=8888)
    try:
        logging.info('starting the server')
        server.start()
    except KeyboardInterrupt:
        logging.debug('canceling the sensor update looping task')
        sensor.cancel_update_level_task()
        logging.info('stopping the server')
        server.stop()
        logging.info('done')


if __name__ == '__main__':
    logging.basicConfig(
        level=10,
        format="%(asctime)s %(filename)s:%(lineno)s %(levelname)s %(message)s"
    )
    run_server()
