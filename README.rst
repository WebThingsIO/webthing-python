webthing
========

Implementation of an HTTP `Web Thing <https://iot.mozilla.org/wot/>`_. This library is compatible with Python 2.7 and Python 3.4+. If using Python 2.7, you must use `zeroconf==0.19.1`.

Example
=======

.. code:: python

    import time
    import uuid

    from webthing import Action, Event, Property, Thing, WebThingServer


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


    def run_server():
        thing = Thing(name='My Lamp', description='A web connected lamp')

        thing.add_property(
            Property(thing,
                     'on',
                     metadata={
                         'type': 'boolean',
                         'description': 'Whether the lamp is turned on',
                     },
                     value=True))
        thing.add_property(
            Property(thing,
                     'level',
                     metadata={
                         'type': 'number',
                         'description': 'The level of light from 0-100',
                         'minimum': 0,
                         'maximum': 100,
                     },
                     value=50))

        thing.add_available_action(
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

        thing.add_available_event(
            'overheated',
            {'description': 'The lamp has exceeded its safe operating temperature',
             'type': 'number',
             'unit': 'celcius'})

        server = WebThingServer(thing, port=8888)
        try:
            server.start()
        except KeyboardInterrupt:
            server.stop()


    if __name__ == '__main__':
        run_server()
