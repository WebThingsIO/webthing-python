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

    def initialize(self, thing):
        """
        Initialize the handler.

        thing -- the Thing managed by this server
        """
        self.thing = thing


class ThingHandler(tornado.websocket.WebSocketHandler):
    """Handle a request to /."""

    def initialize(self, thing, ip, port):
        """
        Initialize the handler.

        thing -- the Thing managed by this server
        ip -- local IP address of the server
        port -- port the server is listening on
        """
        self.thing = thing
        if self.application.is_tls:
            self.ws_path = 'wss://{}:{}/'.format(ip, port)
        else:
            self.ws_path = 'ws://{}:{}/'.format(ip, port)

    @tornado.web.asynchronous
    def get(self, *args, **kwargs):
        """Handle a GET request, including websocket requests."""
        if self.request.headers.get('Upgrade', '').lower() == 'websocket':
            tornado.websocket.WebSocketHandler.get(self, *args, **kwargs)
            return

        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps(
            self.thing.as_thing_description(ws_path=self.ws_path)))
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

    def get(self):
        """
        Handle a GET request.

        TODO: this is not yet defined in the spec
        """
        pass


class PropertyHandler(BaseHandler):
    """Handle a request to /properties/<property>."""

    def get(self, property_name):
        """
        Handle a GET request.

        property_name -- the name of the property from the URL path
        """
        if self.thing.has_property(property_name):
            self.set_header('Content-Type', 'application/json')
            self.write(json.dumps({
                property_name: self.thing.get_property(property_name),
            }))
        else:
            self.set_status(404)

    def put(self, property_name):
        """
        Handle a PUT request.

        property_name -- the name of the property from the URL path
        """
        try:
            args = json.loads(self.request.body)
        except ValueError:
            self.set_status(400)
            return

        if property_name not in args:
            self.set_status(400)
            return

        if self.thing.has_property(property_name):
            self.thing.set_property(property_name, args[property_name])
            self.set_header('Content-Type', 'application/json')
            self.write(json.dumps({
                property_name: self.thing.get_property(property_name),
            }))
        else:
            self.set_status(404)


class ActionsHandler(BaseHandler):
    """Handle a request to /actions."""

    def get(self):
        """Handle a GET request."""
        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps(self.thing.get_action_descriptions()))

    def post(self):
        """Handle a POST request."""
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

            action = self.thing.perform_action(action_name, input_)
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

    def get(self, action_name):
        """
        Handle a GET request.

        TODO: this is not yet defined in the spec

        action_name -- name of the action from the URL path
        """
        pass


class ActionIDHandler(BaseHandler):
    """Handle a request to /actions/<action_name>/<action_id>."""

    def get(self, action_name, action_id):
        """
        Handle a GET request.

        action_name -- name of the action from the URL path
        action_id -- the action ID from the URL path
        """
        action = self.thing.get_action(action_name, action_id)
        if action is None:
            self.set_status(404)
            return

        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps(action.as_action_description()))

    def put(self, action_name, action_id):
        """
        Handle a PUT request.

        TODO: this is not yet defined in the spec

        action_name -- name of the action from the URL path
        action_id -- the action ID from the URL path
        """
        pass

    def delete(self, action_name, action_id):
        """
        Handle a DELETE request.

        action_name -- name of the action from the URL path
        action_id -- the action ID from the URL path
        """
        action = self.thing.get_action(action_name, action_id)
        if action is None:
            self.set_status(404)
            return

        action.cancel()
        self.set_status(204)


class EventsHandler(BaseHandler):
    """Handle a request to /events."""

    def get(self):
        """Handle a GET request."""
        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps(self.thing.get_event_descriptions()))


class EventHandler(BaseHandler):
    """Handle a request to /events/<event_name>."""

    def get(self, event_name):
        """
        Handle a GET request.

        TODO: this is not yet defined in the spec

        event_name -- name of the event from the URL path
        """
        pass


class WebThingServer:
    """Server to represent a Web Thing over HTTP."""

    def __init__(self, thing, port=80, ssl_options=None):
        """
        Initialize the WebThingServer.

        thing -- the Thing managed by this server
        port -- port to listen on (defaults to 80)
        ssl_options -- dict of SSL options to pass to the tornado server
        """
        self.thing = thing
        self.port = port
        self.ip = get_ip()

        self.app = tornado.web.Application([
            (
                r'/?',
                ThingHandler,
                dict(thing=self.thing, ip=self.ip, port=self.port),
            ),
            (
                r'/properties/?',
                PropertiesHandler,
                dict(thing=self.thing),
            ),
            (
                r'/properties/([^/]+)/?',
                PropertyHandler,
                dict(thing=self.thing),
            ),
            (
                r'/actions/?',
                ActionsHandler,
                dict(thing=self.thing),
            ),
            (
                r'/actions/([^/]+)/?',
                ActionHandler,
                dict(thing=self.thing),
            ),
            (
                r'/actions/([^/]+)/([^/]+)/?',
                ActionIDHandler,
                dict(thing=self.thing),
            ),
            (
                r'/events/?',
                EventsHandler,
                dict(thing=self.thing),
            ),
            (
                r'/events/([^/]+)/?',
                EventHandler,
                dict(thing=self.thing),
            ),
        ])
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
            '{}._http._tcp.local.'.format(self.thing.name),
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
