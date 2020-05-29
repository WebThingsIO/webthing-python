"""Python Web Thing server implementation."""

from zeroconf import ServiceInfo, Zeroconf
import json
import socket
import sys
import tornado.concurrent
import tornado.gen
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket

from .errors import PropertyError
from .subscriber import Subscriber
from .utils import get_addresses, get_ip


@tornado.gen.coroutine
def perform_action(action):
    """Perform an Action in a coroutine."""
    action.start()


class SingleThing:
    """A container for a single thing."""

    def __init__(self, thing):
        """
        Initialize the container.

        thing -- the thing to store
        """
        self.thing = thing

    def get_thing(self, _=None):
        """Get the thing at the given index."""
        return self.thing

    def get_things(self):
        """Get the list of things."""
        return [self.thing]

    def get_name(self):
        """Get the mDNS server name."""
        return self.thing.title


class MultipleThings:
    """A container for multiple things."""

    def __init__(self, things, name):
        """
        Initialize the container.

        things -- the things to store
        name -- the mDNS server name
        """
        self.things = things
        self.name = name

    def get_thing(self, idx):
        """
        Get the thing at the given index.

        idx -- the index
        """
        try:
            idx = int(idx)
        except ValueError:
            return None

        if idx < 0 or idx >= len(self.things):
            return None

        return self.things[idx]

    def get_things(self):
        """Get the list of things."""
        return self.things

    def get_name(self):
        """Get the mDNS server name."""
        return self.name


class BaseHandler(tornado.web.RequestHandler):
    """Base handler that is initialized with a thing."""

    def initialize(self, things, hosts):
        """
        Initialize the handler.

        things -- list of Things managed by this server
        hosts -- list of allowed hostnames
        """
        self.things = things
        self.hosts = hosts

    def prepare(self):
        """Validate Host header."""
        host = self.request.headers.get('Host', None)
        if host is not None and host.lower() in self.hosts:
            return

        raise tornado.web.HTTPError(403)

    def get_thing(self, thing_id):
        """
        Get the thing this request is for.

        thing_id -- ID of the thing to get, in string form

        Returns the thing, or None if not found.
        """
        return self.things.get_thing(thing_id)

    def set_default_headers(self, *args, **kwargs):
        """Set the default headers for all requests."""
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers',
                        'Origin, X-Requested-With, Content-Type, Accept')
        self.set_header('Access-Control-Allow-Methods',
                        'GET, HEAD, PUT, POST, DELETE')

    def options(self, *args, **kwargs):
        """Handle an OPTIONS request."""
        self.set_status(204)


class ThingsHandler(BaseHandler):
    """Handle a request to / when the server manages multiple things."""

    def get(self):
        """
        Handle a GET request.

        property_name -- the name of the property from the URL path
        """
        self.set_header('Content-Type', 'application/json')
        ws_href = '{}://{}'.format(
            'wss' if self.request.protocol == 'https' else 'ws',
            self.request.headers.get('Host', '')
        )

        descriptions = []
        for thing in self.things.get_things():
            description = thing.as_thing_description()
            description['href'] = thing.get_href()
            description['links'].append({
                'rel': 'alternate',
                'href': '{}{}'.format(ws_href, thing.get_href()),
            })
            description['base'] = '{}://{}{}'.format(
                self.request.protocol,
                self.request.headers.get('Host', ''),
                thing.get_href()
            )
            description['securityDefinitions'] = {
                'nosec_sc': {
                    'scheme': 'nosec',
                },
            }
            description['security'] = 'nosec_sc'
            descriptions.append(description)

        self.write(json.dumps(descriptions))


class ThingHandler(tornado.websocket.WebSocketHandler, Subscriber):
    """Handle a request to /."""

    def initialize(self, things, hosts):
        """
        Initialize the handler.

        things -- list of Things managed by this server
        hosts -- list of allowed hostnames
        """
        self.things = things
        self.hosts = hosts

    def prepare(self):
        """Validate Host header."""
        host = self.request.headers.get('Host', None)
        if host is not None and host in self.hosts:
            return

        raise tornado.web.HTTPError(403)

    def set_default_headers(self, *args, **kwargs):
        """Set the default headers for all requests."""
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers',
                        'Origin, X-Requested-With, Content-Type, Accept')
        self.set_header('Access-Control-Allow-Methods',
                        'GET, HEAD, PUT, POST, DELETE')

    def options(self, *args, **kwargs):
        """Handle an OPTIONS request."""
        self.set_status(204)

    def get_thing(self, thing_id):
        """
        Get the thing this request is for.

        thing_id -- ID of the thing to get, in string form

        Returns the thing, or None if not found.
        """
        return self.things.get_thing(thing_id)

    @tornado.gen.coroutine
    def get(self, thing_id='0'):
        """
        Handle a GET request, including websocket requests.

        thing_id -- ID of the thing this request is for
        """
        self.thing = self.get_thing(thing_id)
        if self.thing is None:
            self.set_status(404)
            self.finish()
            return

        if self.request.headers.get('Upgrade', '').lower() == 'websocket':
            yield tornado.websocket.WebSocketHandler.get(self)
            return

        self.set_header('Content-Type', 'application/json')
        ws_href = '{}://{}'.format(
            'wss' if self.request.protocol == 'https' else 'ws',
            self.request.headers.get('Host', '')
        )

        description = self.thing.as_thing_description()
        description['links'].append({
            'rel': 'alternate',
            'href': '{}{}'.format(ws_href, self.thing.get_href()),
        })
        description['base'] = '{}://{}{}'.format(
            self.request.protocol,
            self.request.headers.get('Host', ''),
            self.thing.get_href()
        )
        description['securityDefinitions'] = {
            'nosec_sc': {
                'scheme': 'nosec',
            },
        }
        description['security'] = 'nosec_sc'

        self.write(json.dumps(description))
        self.finish()

    def open(self):
        """Handle a new connection."""
        self.thing.add_subscriber(self)

    def on_message(self, message):
        """
        Handle an incoming message.

        message -- message to handle
        """
        try:
            message = json.loads(message)
        except ValueError:
            try:
                self.write_message(json.dumps({
                    'messageType': 'error',
                    'data': {
                        'status': '400 Bad Request',
                        'message': 'Parsing request failed',
                    },
                }))
            except tornado.websocket.WebSocketClosedError:
                pass

            return

        if 'messageType' not in message or 'data' not in message:
            try:
                self.write_message(json.dumps({
                    'messageType': 'error',
                    'data': {
                        'status': '400 Bad Request',
                        'message': 'Invalid message',
                    },
                }))
            except tornado.websocket.WebSocketClosedError:
                pass

            return

        msg_type = message['messageType']
        if msg_type == 'setProperty':
            for property_name, property_value in message['data'].items():
                try:
                    self.thing.set_property(property_name, property_value)
                except PropertyError as e:
                    self.write_message(json.dumps({
                        'messageType': 'error',
                        'data': {
                            'status': '400 Bad Request',
                            'message': str(e),
                        },
                    }))
        elif msg_type == 'requestAction':
            for action_name, action_params in message['data'].items():
                input_ = None
                if 'input' in action_params:
                    input_ = action_params['input']

                action = self.thing.perform_action(action_name, input_)
                if action:
                    tornado.ioloop.IOLoop.current().spawn_callback(
                        perform_action,
                        action,
                    )
                else:
                    self.write_message(json.dumps({
                        'messageType': 'error',
                        'data': {
                            'status': '400 Bad Request',
                            'message': 'Invalid action request',
                            'request': message,
                        },
                    }))
        elif msg_type == 'addEventSubscription':
            for event_name in message['data'].keys():
                self.thing.add_event_subscriber(event_name, self)
        else:
            try:
                self.write_message(json.dumps({
                    'messageType': 'error',
                    'data': {
                        'status': '400 Bad Request',
                        'message': 'Unknown messageType: ' + msg_type,
                        'request': message,
                    },
                }))
            except tornado.websocket.WebSocketClosedError:
                pass

    def on_close(self):
        """Handle a close event on the socket."""
        self.thing.remove_subscriber(self)

    def check_origin(self, origin):
        """Allow connections from all origins."""
        return True

    def update_property(self, property_):
        """
        Send an update about a Property.

        :param property_: Property
        """
        message = json.dumps({
            'messageType': 'propertyStatus',
            'data': {
                property_.name: property_.get_value(),
            }
        })

        self.write_message(message)

    def update_action(self, action):
        """
        Send an update about an Action.

        :param action: Action
        """
        message = json.dumps({
            'messageType': 'actionStatus',
            'data': action.as_action_description(),
        })

        self.write_message(message)

    def update_event(self, event):
        """
        Send an update about an Event.

        :param event: Event
        """
        message = json.dumps({
            'messageType': 'event',
            'data': event.as_event_description(),
        })

        self.write_message(message)


class PropertiesHandler(BaseHandler):
    """Handle a request to /properties."""

    def get(self, thing_id='0'):
        """
        Handle a GET request.

        thing_id -- ID of the thing this request is for
        """
        thing = self.get_thing(thing_id)
        if thing is None:
            self.set_status(404)
            return

        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps(thing.get_properties()))


class PropertyHandler(BaseHandler):
    """Handle a request to /properties/<property>."""

    def get(self, thing_id='0', property_name=None):
        """
        Handle a GET request.

        thing_id -- ID of the thing this request is for
        property_name -- the name of the property from the URL path
        """
        thing = self.get_thing(thing_id)
        if thing is None:
            self.set_status(404)
            return

        if thing.has_property(property_name):
            self.set_header('Content-Type', 'application/json')
            self.write(json.dumps({
                property_name: thing.get_property(property_name),
            }))
        else:
            self.set_status(404)

    def put(self, thing_id='0', property_name=None):
        """
        Handle a PUT request.

        thing_id -- ID of the thing this request is for
        property_name -- the name of the property from the URL path
        """
        thing = self.get_thing(thing_id)
        if thing is None:
            self.set_status(404)
            return

        try:
            args = json.loads(self.request.body.decode())
        except ValueError:
            self.set_status(400)
            return

        if property_name not in args:
            self.set_status(400)
            return

        if thing.has_property(property_name):
            try:
                thing.set_property(property_name, args[property_name])
            except PropertyError:
                self.set_status(400)
                return

            self.set_header('Content-Type', 'application/json')
            self.write(json.dumps({
                property_name: thing.get_property(property_name),
            }))
        else:
            self.set_status(404)


class ActionsHandler(BaseHandler):
    """Handle a request to /actions."""

    def get(self, thing_id='0'):
        """
        Handle a GET request.

        thing_id -- ID of the thing this request is for
        """
        thing = self.get_thing(thing_id)
        if thing is None:
            self.set_status(404)
            return

        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps(thing.get_action_descriptions()))

    def post(self, thing_id='0'):
        """
        Handle a POST request.

        thing_id -- ID of the thing this request is for
        """
        thing = self.get_thing(thing_id)
        if thing is None:
            self.set_status(404)
            return

        try:
            message = json.loads(self.request.body.decode())
        except ValueError:
            self.set_status(400)
            return

        keys = list(message.keys())
        if len(keys) != 1:
            self.set_status(400)
            return

        action_name = keys[0]
        action_params = message[action_name]
        input_ = None
        if 'input' in action_params:
            input_ = action_params['input']

        action = thing.perform_action(action_name, input_)
        if action:
            response = action.as_action_description()

            # Start the action
            tornado.ioloop.IOLoop.current().spawn_callback(
                perform_action,
                action,
            )

            self.set_status(201)
            self.write(json.dumps(response))
        else:
            self.set_status(400)


class ActionHandler(BaseHandler):
    """Handle a request to /actions/<action_name>."""

    def get(self, thing_id='0', action_name=None):
        """
        Handle a GET request.

        thing_id -- ID of the thing this request is for
        action_name -- name of the action from the URL path
        """
        thing = self.get_thing(thing_id)
        if thing is None:
            self.set_status(404)
            return

        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps(thing.get_action_descriptions(
            action_name=action_name)))

    def post(self, thing_id='0', action_name=None):
        """
        Handle a POST request.

        thing_id -- ID of the thing this request is for
        """
        thing = self.get_thing(thing_id)
        if thing is None:
            self.set_status(404)
            return

        try:
            message = json.loads(self.request.body.decode())
        except ValueError:
            self.set_status(400)
            return

        keys = list(message.keys())
        if len(keys) != 1:
            self.set_status(400)
            return

        if keys[0] != action_name:
            self.set_status(400)
            return

        action_params = message[action_name]
        input_ = None
        if 'input' in action_params:
            input_ = action_params['input']

        action = thing.perform_action(action_name, input_)
        if action:
            response = action.as_action_description()

            # Start the action
            tornado.ioloop.IOLoop.current().spawn_callback(
                perform_action,
                action,
            )

            self.set_status(201)
            self.write(json.dumps(response))
        else:
            self.set_status(400)


class ActionIDHandler(BaseHandler):
    """Handle a request to /actions/<action_name>/<action_id>."""

    def get(self, thing_id='0', action_name=None, action_id=None):
        """
        Handle a GET request.

        thing_id -- ID of the thing this request is for
        action_name -- name of the action from the URL path
        action_id -- the action ID from the URL path
        """
        thing = self.get_thing(thing_id)
        if thing is None:
            self.set_status(404)
            return

        action = thing.get_action(action_name, action_id)
        if action is None:
            self.set_status(404)
            return

        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps(action.as_action_description()))

    def put(self, thing_id='0', action_name=None, action_id=None):
        """
        Handle a PUT request.

        TODO: this is not yet defined in the spec

        thing_id -- ID of the thing this request is for
        action_name -- name of the action from the URL path
        action_id -- the action ID from the URL path
        """
        thing = self.get_thing(thing_id)
        if thing is None:
            self.set_status(404)
            return

        self.set_status(200)

    def delete(self, thing_id='0', action_name=None, action_id=None):
        """
        Handle a DELETE request.

        thing_id -- ID of the thing this request is for
        action_name -- name of the action from the URL path
        action_id -- the action ID from the URL path
        """
        thing = self.get_thing(thing_id)
        if thing is None:
            self.set_status(404)
            return

        if thing.remove_action(action_name, action_id):
            self.set_status(204)
        else:
            self.set_status(404)


class EventsHandler(BaseHandler):
    """Handle a request to /events."""

    def get(self, thing_id='0'):
        """
        Handle a GET request.

        thing_id -- ID of the thing this request is for
        """
        thing = self.get_thing(thing_id)
        if thing is None:
            self.set_status(404)
            return

        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps(thing.get_event_descriptions()))


class EventHandler(BaseHandler):
    """Handle a request to /events/<event_name>."""

    def get(self, thing_id='0', event_name=None):
        """
        Handle a GET request.

        thing_id -- ID of the thing this request is for
        event_name -- name of the event from the URL path
        """
        thing = self.get_thing(thing_id)
        if thing is None:
            self.set_status(404)
            return

        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps(thing.get_event_descriptions(
            event_name=event_name)))


class WebThingServer:
    """Server to represent a Web Thing over HTTP."""

    def __init__(self, things, port=80, hostname=None, ssl_options=None,
                 additional_routes=None, base_path=''):
        """
        Initialize the WebThingServer.

        For documentation on the additional route format, see:
        https://www.tornadoweb.org/en/stable/web.html#tornado.web.Application

        things -- things managed by this server -- should be of type
                  SingleThing or MultipleThings
        port -- port to listen on (defaults to 80)
        hostname -- Optional host name, i.e. mything.com
        ssl_options -- dict of SSL options to pass to the tornado server
        additional_routes -- list of additional routes to add to the server
        base_path -- base URL path to use, rather than '/'
        """
        self.things = things
        self.name = things.get_name()
        self.port = port
        self.hostname = hostname
        self.base_path = base_path.rstrip('/')

        system_hostname = socket.gethostname().lower()
        self.hosts = [
            'localhost',
            'localhost:{}'.format(self.port),
            '{}.local'.format(system_hostname),
            '{}.local:{}'.format(system_hostname, self.port),
        ]

        for address in get_addresses():
            self.hosts.extend([
                address,
                '{}:{}'.format(address, self.port),
            ])

        if self.hostname is not None:
            self.hostname = self.hostname.lower()
            self.hosts.extend([
                self.hostname,
                '{}:{}'.format(self.hostname, self.port),
            ])

        if isinstance(self.things, MultipleThings):
            for idx, thing in enumerate(self.things.get_things()):
                thing.set_href_prefix('{}/{}'.format(self.base_path, idx))

            handlers = [
                [
                    r'/?',
                    ThingsHandler,
                    dict(things=self.things, hosts=self.hosts),
                ],
                [
                    r'/(?P<thing_id>\d+)/?',
                    ThingHandler,
                    dict(things=self.things, hosts=self.hosts),
                ],
                [
                    r'/(?P<thing_id>\d+)/properties/?',
                    PropertiesHandler,
                    dict(things=self.things, hosts=self.hosts),
                ],
                [
                    r'/(?P<thing_id>\d+)/properties/' +
                    r'(?P<property_name>[^/]+)/?',
                    PropertyHandler,
                    dict(things=self.things, hosts=self.hosts),
                ],
                [
                    r'/(?P<thing_id>\d+)/actions/?',
                    ActionsHandler,
                    dict(things=self.things, hosts=self.hosts),
                ],
                [
                    r'/(?P<thing_id>\d+)/actions/(?P<action_name>[^/]+)/?',
                    ActionHandler,
                    dict(things=self.things, hosts=self.hosts),
                ],
                [
                    r'/(?P<thing_id>\d+)/actions/' +
                    r'(?P<action_name>[^/]+)/(?P<action_id>[^/]+)/?',
                    ActionIDHandler,
                    dict(things=self.things, hosts=self.hosts),
                ],
                [
                    r'/(?P<thing_id>\d+)/events/?',
                    EventsHandler,
                    dict(things=self.things, hosts=self.hosts),
                ],
                [
                    r'/(?P<thing_id>\d+)/events/(?P<event_name>[^/]+)/?',
                    EventHandler,
                    dict(things=self.things, hosts=self.hosts),
                ],
            ]
        else:
            self.things.get_thing().set_href_prefix(self.base_path)
            handlers = [
                [
                    r'/?',
                    ThingHandler,
                    dict(things=self.things, hosts=self.hosts),
                ],
                [
                    r'/properties/?',
                    PropertiesHandler,
                    dict(things=self.things, hosts=self.hosts),
                ],
                [
                    r'/properties/(?P<property_name>[^/]+)/?',
                    PropertyHandler,
                    dict(things=self.things, hosts=self.hosts),
                ],
                [
                    r'/actions/?',
                    ActionsHandler,
                    dict(things=self.things, hosts=self.hosts),
                ],
                [
                    r'/actions/(?P<action_name>[^/]+)/?',
                    ActionHandler,
                    dict(things=self.things, hosts=self.hosts),
                ],
                [
                    r'/actions/(?P<action_name>[^/]+)/(?P<action_id>[^/]+)/?',
                    ActionIDHandler,
                    dict(things=self.things, hosts=self.hosts),
                ],
                [
                    r'/events/?',
                    EventsHandler,
                    dict(things=self.things, hosts=self.hosts),
                ],
                [
                    r'/events/(?P<event_name>[^/]+)/?',
                    EventHandler,
                    dict(things=self.things, hosts=self.hosts),
                ],
            ]

        if isinstance(additional_routes, list):
            handlers = additional_routes + handlers

        if self.base_path:
            for h in handlers:
                h[0] = self.base_path + h[0]

        self.app = tornado.web.Application(handlers)
        self.app.is_tls = ssl_options is not None
        self.server = tornado.httpserver.HTTPServer(self.app,
                                                    ssl_options=ssl_options)

    def start(self):
        """Start listening for incoming connections."""
        args = [
            '_webthing._tcp.local.',
            '{}._webthing._tcp.local.'.format(self.name),
        ]
        kwargs = {
            'port': self.port,
            'properties': {
                'path': '/',
            },
            'server': '{}.local.'.format(socket.gethostname()),
        }

        if sys.version_info.major == 3:
            kwargs['addresses'] = [socket.inet_aton(get_ip())]
        else:
            kwargs['address'] = socket.inet_aton(get_ip())

        self.service_info = ServiceInfo(*args, **kwargs)
        self.zeroconf = Zeroconf()
        self.zeroconf.register_service(self.service_info)

        self.server.listen(self.port)
        tornado.ioloop.IOLoop.current().start()

    def stop(self):
        """Stop listening."""
        self.zeroconf.unregister_service(self.service_info)
        self.zeroconf.close()
        self.server.stop()
