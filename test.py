from webthing import Property, Thing, WebThingServer


if __name__ == '__main__':
    thing = Thing('pi', description='A WoT-connected Raspberry Pi')

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

    server = WebThingServer(port=8888)
    server.add_thing(thing)
    server.start()
