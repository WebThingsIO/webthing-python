webthing
========

Implementation of an HTTP `Web Thing <https://iot.mozilla.org/wot/>`_. This library is compatible with Python 2.7 and Python 3.4+. If using Python 2.7, you must use ``zeroconf==0.19.1``.

Installation
============

``webthing`` can be installed via ``pip``, as such:

.. code:: shell

  $ pip install webthing

Example
=======

In this example we will set up a dimmable light and a humidity sensor (both using fake data, of course). Both working examples can be found in `here <https://github.com/mozilla-iot/webthing-java/tree/master/src/main/java/org/mozilla/iot/webthing/example>`_.

Dimmable Light
--------------

Imagine you have a dimmable Light that you want to expose via the web of things API. The Light can be turned on/off and the brightness can be set from 0% to 100%. Besides the name, description, and type, a `dimmableLight` is required to expose two properties:

* ``on``: the state of the light, whether it is turned on or off

  - Setting this property via a ``PUT {"on": true/false}`` call to the REST API toggles the light.

* ``level``: the brightness level of the light from 0-100%

  - Setting this property via a PUT call to the REST API sets the brightness level of this light.

First we create a new Thing:

.. code:: python

    light = Thing('My Lamp', 'dimmableLight', 'A web connected lamp')

Now we can add the required properties.

The ``on`` property reports and sets the on/off state of the light. For this, we need to have a ``Value`` Object which holds the actual state and also how to turn the light on/off. For our purposes, we just want to log the new state if the light is switched on/off.

.. code:: python

  light.add_property(
      Property(
          light,
          'on',
          Value(True, lambda v: print('On-State is now', v)),
          metadata={
              'type': 'boolean',
              'description': 'Whether the lamp is turned on',
          }))

The ``level`` property reports the brightness level of the light and sets the level. Like before, instead of actually setting the level of a light, we just log the level to std::out.

.. code:: python

  light.add_property(
      Property(
          light,
          'level',
          Value(0.0, lambda l: print('New light level is', l)),
          metadata={
              'type': 'number',
              'description': 'The level of light from 0-100',
              'minimum': 0,
              'maximum': 100,
          }))

Now we can add our newly created thing to the server and start it:

.. code:: python

  # If adding more than one thing here, be sure to set the second
  # parameter to some string, which will be broadcast via mDNS.
  # In the single thing case, the thing's name will be broadcast.
  server = WebThingServer([light], port=8888)

  try:
      server.start()
  except KeyboardInterrupt:
      server.stop()

This will start the server, making the light available via the WoT REST API and announcing it as a discoverable resource on your local network via mDNS.

Sensor
------

Let's now also connect a humidity sensor to the server we set up for our light.

A ``multiLevelSensor`` (a sensor that can also return a level instead of just true/false) has two required properties (besides the name, type, and  optional description): ``on`` and ``level``. We want to monitor those properties and get notified if the value changes.

First we create a new Thing:

.. code:: python

  sensor = Thing('My Humidity Sensor',
                 'multiLevelSensor',
                 'A web connected humidity sensor')

Then we create and add the appropriate properties:

* ``on``: tells us whether the sensor is on (i.e. high), or off (i.e. low)

  .. code:: python

    sensor.add_property(
        Property(
            sensor,
            'on',
            Value(True),
            metadata={
                'type': 'boolean',
                'description': 'Whether the sensor is on',
            }))

* ``level``: tells us what the sensor is actually reading

  - Contrary to the light, the value cannot be set via an API call, as it wouldn't make much sense, to SET what a sensor is reading. Therefore, we are utilizing a **read-only** Value by omitting the ``setter`` parameter.

    .. code:: python

      level = Value(0.0);

      sensor.add_property(
          Property(
              sensor,
              'level',
              level,
              metadata={
                  'type': 'number',
                  'description': 'The current humidity in %',
                  'unit': '%',
              }))

Now we have a sensor that constantly reports 0%. To make it usable, we need a thread or some kind of input when the sensor has a new reading available. For this purpose we start a thread that queries the physical sensor every few seconds. For our purposes, it just calls a fake method.

.. code:: python

  def update_level():
      while True:
          time.sleep(3)

          # Update the underlying value, which in turn notifies all listeners
          level.notify_of_external_update(read_from_gpio())

  t = threading.Thread(target=update_level)
  t.daemon = True
  t.start()

This will update our ``Value`` object with the sensor readings via the ``level.notify_of_external_update(read_from_gpio())`` call. The ``Value`` object now notifies the property and the thing that the value has changed, which in turn notifies all websocket listeners.