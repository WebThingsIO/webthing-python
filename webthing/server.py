"""Python Web Thing server implementation."""

from zeroconf import ServiceInfo, Zeroconf
import json
import socket
import tornado.concurrent
import tornado.gen
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket

from .utils import get_ip


@tornado.gen.coroutine
def perform_action(action):
    """Perform an Action in a coroutine."""
    action.start()


class BaseHandler(tornado.web.RequestHandler):
    """Base handler that is initialized with a thing."""

    def initialize(self, things):
        """
        Initialize the handler.

        things -- list of Things managed by this server
        """
        self.things = things

    def get_thing(self, thing_id):
        """
        Get the thing this request is for.

        thing_id -- ID of the thing to get, in string form

        Returns the thing, or None if not found.
        """
        if len(self.things) > 1:
            try:
                thing_id = int(thing_id)
            except ValueError:
                return None

            if thing_id >= len(self.things):
                return None

            return self.things[thing_id]
        else:
            return self.things[0]


class ThingsHandler(BaseHandler):
    """Handle a request to / when the server manages multiple things."""

    def get(self):
        """
        Handle a GET request.

        property_name -- the name of the property from the URL path
        """
        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps([
            thing.as_thing_description()
            for idx, thing in enumerate(self.things)
        ]))


class ThingHandler(tornado.websocket.WebSocketHandler):
    """Handle a request to /."""

    def initialize(self, things):
        """
        Initialize the handler.

        things -- list of Things managed by this server
        """
        self.things = things

    def get_thing(self, thing_id):
        """
        Get the thing this request is for.

        thing_id -- ID of the thing to get, in string form

        Returns the thing, or None if not found.
        """
        if len(self.things) > 1:
            try:
                thing_id = int(thing_id)
            except ValueError:
                return None

            if thing_id >= len(self.things):
                return None

            return self.things[thing_id]
        else:
            return self.things[0]

    @tornado.web.asynchronous
    def get(self, thing_id='0'):
        """
        Handle a GET request, including websocket requests.

        thing_id -- ID of the thing this request is for
        """
        self.thing = self.get_thing(thing_id)
        if self.thing is None:
            self.set_status(404)
            return

        if self.request.headers.get('Upgrade', '').lower() == 'websocket':
            tornado.websocket.WebSocketHandler.get(self)
            return

        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps(self.thing.as_thing_description()))
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
                self.thing.set_property(property_name, property_value)
        elif msg_type == 'requestAction':
            for action_name, action_params in message['data'].items():
                input_ = None
                if 'input' in action_params:
                    input_ = action_params['input']

                action = self.thing.perform_action(action_name, input_)
                tornado.ioloop.IOLoop.current().spawn_callback(
                    perform_action,
                    action,
                )
        elif msg_type == 'addEventSubscription':
            for event_name in message['data'].keys():
                self.thing.add_event_subscriber(event_name, self)
        else:
            try:
                self.send_message(json.dumps({
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


class PropertiesHandler(BaseHandler):
    """Handle a request to /properties."""

    def get(self, thing_id='0'):
        """
        Handle a GET request.

        TODO: this is not yet defined in the spec

        thing_id -- ID of the thing this request is for
        """
        thing_id = int(thing_id)
        if thing_id >= len(self.things):
            self.set_status(404)
            return

        pass


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
            args = json.loads(self.request.body)
        except ValueError:
            self.set_status(400)
            return

        if property_name not in args:
            self.set_status(400)
            return

        if thing.has_property(property_name):
            thing.set_property(property_name, args[property_name])
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
            message = json.loads(self.request.body)
        except ValueError:
            self.set_status(400)
            return

        response = {}
        for action_name, action_params in message.items():
            input_ = None
            if 'input' in action_params:
                input_ = action_params['input']

            action = thing.perform_action(action_name, input_)
            response.update(action.as_action_description())

            # Start the action
            tornado.ioloop.IOLoop.current().spawn_callback(
                perform_action,
                action,
            )

        self.set_status(201)
        self.write(json.dumps(response))


class ActionHandler(BaseHandler):
    """Handle a request to /actions/<action_name>."""

    def get(self, thing_id='0', action_name=None):
        """
        Handle a GET request.

        TODO: this is not yet defined in the spec

        thing_id -- ID of the thing this request is for
        action_name -- name of the action from the URL path
        """
        thing = self.get_thing(thing_id)
        if thing is None:
            self.set_status(404)
            return

        self.set_status(200)


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

        action = thing.get_action(action_name, action_id)
        if action is None:
            self.set_status(404)
            return

        action.cancel()
        self.set_status(204)


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

        TODO: this is not yet defined in the spec

        thing_id -- ID of the thing this request is for
        event_name -- name of the event from the URL path
        """
        thing = self.get_thing(thing_id)
        if thing is None:
            self.set_status(404)
            return

        self.set_status(200)


class WebThingServer:
    """Server to represent a Web Thing over HTTP."""

    def __init__(self, things, name=None, port=80, ssl_options=None):
        """
        Initialize the WebThingServer.

        things -- list of Things managed by this server
        name -- name of this device -- this is only needed if the server is
                managing multiple things
        port -- port to listen on (defaults to 80)
        ssl_options -- dict of SSL options to pass to the tornado server
        """
        if type(things) is not list:
            things = [things]

        self.things = things
        self.port = port
        self.ip = get_ip()

        if len(self.things) > 1 and not name:
            raise Exception('name must be set when managing multiple things')

        if len(self.things) > 1:
            for idx, thing in enumerate(self.things):
                thing.set_href_prefix('/{}'.format(idx))
                thing.set_ws_href('{}://{}:{}/{}'.format(
                    'wss' if ssl_options is not None else 'ws',
                    self.ip,
                    self.port,
                    idx))

            self.name = name
            handlers = [
                (
                    r'/?',
                    ThingsHandler,
                    dict(things=self.things),
                ),
                (
                    r'/(?P<thing_id>\d+)/?',
                    ThingHandler,
                    dict(things=self.things),
                ),
                (
                    r'/(?P<thing_id>\d+)/properties/?',
                    PropertiesHandler,
                    dict(things=self.things),
                ),
                (
                    r'/(?P<thing_id>\d+)/properties/(?P<property_name>[^/]+)/?',
                    PropertyHandler,
                    dict(things=self.things),
                ),
                (
                    r'/(?P<thing_id>\d+)/actions/?',
                    ActionsHandler,
                    dict(things=self.things),
                ),
                (
                    r'/(?P<thing_id>\d+)/actions/(?P<action_name>[^/]+)/?',
                    ActionHandler,
                    dict(things=self.things),
                ),
                (
                    r'/(?P<thing_id>\d+)/actions/(?P<action_name>[^/]+)/(?P<action_id>[^/]+)/?',
                    ActionIDHandler,
                    dict(things=self.things),
                ),
                (
                    r'/(?P<thing_id>\d+)/events/?',
                    EventsHandler,
                    dict(things=self.things),
                ),
                (
                    r'/(?P<thing_id>\d+)/events/(?P<event_name>[^/]+)/?',
                    EventHandler,
                    dict(things=self.things),
                ),
            ]
        else:
            self.things[0].set_ws_href('{}://{}:{}'.format(
                'wss' if ssl_options is not None else 'ws',
                self.ip,
                self.port))

            self.name = self.things[0].name
            handlers = [
                (
                    r'/?',
                    ThingHandler,
                    dict(things=self.things),
                ),
                (
                    r'/properties/?',
                    PropertiesHandler,
                    dict(things=self.things),
                ),
                (
                    r'/properties/(?P<property_name>[^/]+)/?',
                    PropertyHandler,
                    dict(things=self.things),
                ),
                (
                    r'/actions/?',
                    ActionsHandler,
                    dict(things=self.things),
                ),
                (
                    r'/actions/(?P<action_name>[^/]+)/?',
                    ActionHandler,
                    dict(things=self.things),
                ),
                (
                    r'/actions/(?P<action_name>[^/]+)/(?P<action_id>[^/]+)/?',
                    ActionIDHandler,
                    dict(things=self.things),
                ),
                (
                    r'/events/?',
                    EventsHandler,
                    dict(things=self.things),
                ),
                (
                    r'/events/(?P<event_name>[^/]+)/?',
                    EventHandler,
                    dict(things=self.things),
                ),
            ]

        self.app = tornado.web.Application(handlers)
        self.app.is_tls = ssl_options is not None
        self.server = tornado.httpserver.HTTPServer(self.app,
                                                    ssl_options=ssl_options)

    def start(self):
        """Start listening for incoming connections."""
        url = '{}://{}:{}/'.format('https' if self.app.is_tls else 'http',
                                   self.ip,
                                   self.port)
        self.service_info = ServiceInfo(
            '_webthing._sub._http._tcp.local.',
            '{}._http._tcp.local.'.format(self.name),
            address=socket.inet_aton(self.ip),
            port=self.port,
            properties={
                'url': url,
            },
            server='{}.local.'.format(socket.gethostname()))
        self.zeroconf = Zeroconf()
        self.zeroconf.register_service(self.service_info)

        self.server.listen(self.port)
        tornado.ioloop.IOLoop.current().start()

    def stop(self):
        """Stop listening."""
        self.zeroconf.unregister_service(self.service_info)
        self.zeroconf.close()
        self.server.stop()
