import random
import time
import uuid
import logging

from asyncio import sleep, CancelledError, get_event_loop

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


class ExampleDimmableLight(Thing):
    """A dimmable light that logs received commands to stdout."""

    def __init__(self):
        super(ExampleDimmableLight, self).__init__('My Lamp',
                                                   'dimmableLight',
                                                   'A web connected lamp')

        self.add_available_action(
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

        self.add_available_event(
            'overheated',
            {'description':
             'The lamp has exceeded its safe operating temperature',
             'type': 'number',
             'unit': 'celsius'})

        self.add_property(self.get_on_property())
        self.add_property(self.get_level_property())

    def get_on_property(self):
        return Property(self,
                        'on',
                        Value(True, lambda v: print('On-State is now', v)),
                        metadata={
                            'type': 'boolean',
                            'description': 'Whether the lamp is turned on',
                        })

    def get_level_property(self):
        return Property(self,
                        'level',
                        Value(50, lambda l: print('New light level is', l)),
                        metadata={
                            'type': 'number',
                            'description': 'The level of light from 0-100',
                            'minimum': 0,
                            'maximum': 100,
                        })


class FakeGpioHumiditySensor(Thing):
    """A humidity sensor which updates its measurement every few seconds."""

    def __init__(self):
        super(FakeGpioHumiditySensor, self).__init__('My Humidity Sensor',
                                                     'multiLevelSensor',
                                                     'A web connected humidity sensor')

        self.add_property(
            Property(self,
                     'on',
                     Value(True),
                     metadata={
                         'type': 'boolean',
                         'description': 'Whether the sensor is on',
                     }))

        self.level = Value(0.0)
        self.add_property(
            Property(self,
                     'level',
                     self.level,
                     metadata={
                         'type': 'number',
                         'description': 'The current humidity in %',
                         'unit': '%',
                     }))
        logging.debug('staring the sensor update looping task')
        self.sensor_update_task = get_event_loop().create_task(self.update_level())

    async def update_level(self):
        try:
            while True:
                await sleep(3)
                new_level = self.read_from_gpio()
                logging.debug('setting new humidity level: %s', new_level)
                self.level.notify_of_external_update(new_level)
        except CancelledError:
            # we have no cleanup to do on cancelation so we can just halt
            # the propagation of the cancelation exception and let the method end.
            pass

    def cancel_update_level_task(self):
        self.sensor_update_task.cancel()
        get_event_loop().run_until_complete(self.sensor_update_task)

    @staticmethod
    def read_from_gpio():
        """Mimic an actual sensor updating its reading every couple seconds."""
        return 70.0 * random.random() * (-0.5 + random.random())


def run_server():
    # Create a thing that represents a dimmable light
    light = ExampleDimmableLight()

    # Create a thing that represents a humidity sensor
    sensor = FakeGpioHumiditySensor()

    # If adding more than one thing here, be sure to set the `name`
    # parameter to some string, which will be broadcast via mDNS.
    # In the single thing case, the thing's name will be broadcast.
    server = WebThingServer([light, sensor],
                            name='LightAndTempDevice',
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
