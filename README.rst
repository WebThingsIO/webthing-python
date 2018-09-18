webthing
========

.. image:: https://travis-ci.org/mozilla-iot/webthing-python.svg?branch=master
    :target: https://travis-ci.org/mozilla-iot/webthing-python
.. image:: https://img.shields.io/pypi/v/webthing.svg
    :target: https://pypi.org/project/webthing/
.. image:: https://img.shields.io/badge/license-MPL--2.0-blue.svg
    :target: https://github.com/mozilla-iot/webthing-python/blob/master/LICENSE.txt

Implementation of an HTTP `Web Thing <https://iot.mozilla.org/wot/>`_. This library is compatible with Python 3.5+.

Installation
============

``webthing`` can be installed via ``pip``, as such:

.. code:: shell

  $ pip install webthing

Example
=======

In this example we will set up a dimmable light and a humidity sensor (both using fake data, of course). Both working examples can be found in `here <https://github.com/mozilla-iot/webthing-python/tree/master/example>`_.

Dimmable Light
--------------

Imagine you have a dimmable light that you want to expose via the web of things API. The light can be turned on/off and the brightness can be set from 0% to 100%. Besides the name, description, and type, a ``Light`` is required to expose two properties:

* ``on``: the state of the light, whether it is turned on or off

  - Setting this property via a ``PUT {"on": true/false}`` call to the REST API toggles the light.

* ``brightness``: the brightness level of the light from 0-100%

  - Setting this property via a PUT call to the REST API sets the brightness level of this light.

First we create a new Thing:

.. code:: python

    light = Thing('My Lamp', ['OnOffSwitch', 'Light'], 'A web connected lamp')

Now we can add the required properties.

The ``on`` property reports and sets the on/off state of the light. For this, we need to have a ``Value`` object which holds the actual state and also a method to turn the light on/off. For our purposes, we just want to log the new state if the light is switched on/off.

.. code:: python

  light.add_property(
      Property(
          light,
          'on',
          Value(True, lambda v: print('On-State is now', v)),
          metadata={
              '@type': 'OnOffProperty', 
              'label': 'On/Off',
              'type': 'boolean',
              'description': 'Whether the lamp is turned on',
          }))

The ``brightness`` property reports the brightness level of the light and sets the level. Like before, instead of actually setting the level of a light, we just log the level.

.. code:: python

  light.add_property(
      Property(
          light,
          'brightness',
          Value(50, lambda v: print('Brightness is now', v)),
          metadata={
              '@type': 'BrightnessProperty',
              'label': 'Brightness',
              'type': 'number',
              'description': 'The level of light from 0-100',
              'minimum': 0,
              'maximum': 100,
              'unit': 'percent',
          }))

Now we can add our newly created thing to the server and start it:

.. code:: python

  # If adding more than one thing, use MultipleThings() with a name.
  # In the single thing case, the thing's name will be broadcast.
  server = WebThingServer(SingleThing(light), port=8888)

  try:
      server.start()
  except KeyboardInterrupt:
      server.stop()

This will start the server, making the light available via the WoT REST API and announcing it as a discoverable resource on your local network via mDNS.

Sensor
------

Let's now also connect a humidity sensor to the server we set up for our light.

A ``MultiLevelSensor`` (a sensor that returns a level instead of just on/off) has one required property (besides the name, type, and optional description): ``level``. We want to monitor this property and get notified if the value changes.

First we create a new Thing:

.. code:: python

  sensor = Thing('My Humidity Sensor',
                 ['MultiLevelSensor'],
                 'A web connected humidity sensor')

Then we create and add the appropriate property:

* ``level``: tells us what the sensor is actually reading

  - Contrary to the light, the value cannot be set via an API call, as it wouldn't make much sense, to SET what a sensor is reading. Therefore, we are creating a **readOnly** property.

    .. code:: python

      level = Value(0.0);

      sensor.add_property(
          Property(
              sensor,
              'level',
              level,
              metadata={
                  '@type': 'LevelProperty',
                  'label': 'Humidity',
                  'type': 'number',
                  'description': 'The current humidity in %',
                  'minimum': 0,
                  'maximum': 100,
                  'unit': 'percent',
                  'readOnly': True,
              }))

Now we have a sensor that constantly reports 0%. To make it usable, we need a thread or some kind of input when the sensor has a new reading available. For this purpose we start a thread that queries the physical sensor every few seconds. For our purposes, it just calls a fake method.

.. code:: python

  self.sensor_update_task = \
      get_event_loop().create_task(self.update_level())

  async def update_level(self):
      try:
          while True:
              await sleep(3)
              new_level = self.read_from_gpio()
              logging.debug('setting new humidity level: %s', new_level)
              self.level.notify_of_external_update(new_level)
      except CancelledError:
          pass

This will update our ``Value`` object with the sensor readings via the ``self.level.notify_of_external_update(read_from_gpio())`` call. The ``Value`` object now notifies the property and the thing that the value has changed, which in turn notifies all websocket listeners.
