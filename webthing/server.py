"""Python Web Thing server implementation."""

import json
import tornado.ioloop
import tornado.web
import tornado.websocket

from .utils import get_ip


class BaseHandler(tornado.web.RequestHandler):
    """Base handler that is initialized with things."""

    def initialize(self, things, ip, port):
        """
        Initialize the handler.

        things -- dict of things managed by the server
        ip -- local IP address of the server
        port -- port the server is listening on
        """
        self.things = things
        self.ws_path = 'ws://{}:{}'.format(ip, port)


class ThingsHandler(BaseHandler):
    """Handle a request to /things."""

    def get(self):
        """Handle a GET request."""
        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps([t.as_thing(ws_path=self.ws_path)
                               for t in self.things.values()]))


class ThingHandler(tornado.websocket.WebSocketHandler):
    """Handle a request to /things/<thing>."""

    def initialize(self, things, ip, port):
        """
        Initialize the handler.

        things -- dict of things managed by the server
        ip -- local IP address of the server
        port -- port the server is listening on
        """
        self.things = things
        self.ws_path = 'ws://{}:{}'.format(ip, port)
        self.thing_name = None

    @tornado.web.asynchronous
    def get(self, *args, **kwargs):
        """Handle a GET request."""
        if self.request.headers.get('Upgrade', '').lower() == 'websocket':
            tornado.websocket.WebSocketHandler.get(self, *args, **kwargs)
            return

        thing_name = args[0]
        if thing_name in self.things:
            self.set_header('Content-Type', 'application/json')
            self.write(json.dumps(
                self.things[thing_name].as_thing(ws_path=self.ws_path)))
        else:
            self.set_status(404)

        self.finish()

    def open(self, thing_name):
        """
        Handle a new connection.

        thing_name -- the name of the thing from the URL path
        """
        self.thing_name = thing_name

    def on_message(self, message):
        """
        Handle an incoming message.

        message -- message to handle
        """
        if self.thing_name not in self.things:
            self.send_message(json.dumps({
                'messageType': 'error',
                'data': {
                    'status': '404 Not Found',
                    'message': 'Thing ' + self.thing_name + ' not found',
                },
            }))
            return

        thing = self.things[self.thing_name]

        try:
            message = json.loads(message)
        except ValueError:
            self.send_message(json.dumps({
                'messageType': 'error',
                'data': {
                    'status': '400 Bad Request',
                    'message': 'Parsing request failed',
                },
            }))
            return

        if 'messageType' not in message or 'data' not in message:
            self.send_message(json.dumps({
                'messageType': 'error',
                'data': {
                    'status': '400 Bad Request',
                    'message': 'Invalid message',
                },
            }))
            return

        msg_type = message['messageType']
        if msg_type == 'setProperty':
            for property_name, property_value in message['data'].items():
                thing.set_property(property_name, property_value)
        elif msg_type == 'requestAction':
            pass
        elif msg_type == 'addEventSubscription':
            pass
        else:
            self.send_message(json.dumps({
                'messageType': 'error',
                'data': {
                    'status': '400 Bad Request',
                    'message': 'Unknown messageType: ' + msg_type,
                    'request': message,
                },
            }))

    def on_close(self):
        """Handle a close event on the socket."""
        pass

    def check_origin(self, origin):
        """Allow connections from all origins."""
        return True


class PropertiesHandler(BaseHandler):
    """Handle a request to /things/<thing>/properties."""

    def get(self, thing_name):
        """
        Handle a GET request.

        thing_name -- the name of the thing from the URL path
        """
        pass


class PropertyHandler(BaseHandler):
    """Handle a request to /things/<thing>/properties/<property>."""

    def get(self, thing_name, property_name):
        """
        Handle a GET request.

        thing_name -- the name of the thing from the URL path
        property_name -- the name of the property from the URL path
        """
        if thing_name in self.things:
            thing = self.things[thing_name]
            if thing.has_property(property_name):
                self.set_header('Content-Type', 'application/json')
                self.write(json.dumps({
                    property_name: thing.get_property(property_name),
                }))
                return

        self.set_status(404)

    def put(self, thing_name, property_name):
        """
        Handle a PUT request.

        thing_name -- the name of the thing from the URL path
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

        if thing_name in self.things:
            thing = self.things[thing_name]
            if thing.has_property(property_name):
                thing.set_property(property_name, args[property_name])
                self.set_status(200)
                return

        self.set_status(404)


class ActionsHandler(BaseHandler):
    """Handle a request to /things/<thing>/actions."""

    def get(self, thing_name):
        """
        Handle a GET request.

        thing_name -- the name of the thing from the URL path
        """
        pass

    def post(self, thing_name):
        """
        Handle a POST request.

        thing_name -- the name of the thing from the URL path
        """
        pass


class ActionHandler(BaseHandler):
    """Handle a request to /things/<thing>/actions/<action>."""

    def get(self, thing_name, action_id):
        """
        Handle a GET request.

        thing_name -- the name of the thing from the URL path
        action_id -- the action ID from the URL path
        """
        pass

    def put(self, thing_name, action_id):
        """
        Handle a PUT request.

        thing_name -- the name of the thing from the URL path
        action_id -- the action ID from the URL path
        """
        pass

    def delete(self, thing_name, action_id):
        """
        Handle a DELETE request.

        thing_name -- the name of the thing from the URL path
        action_id -- the action ID from the URL path
        """
        pass


class EventsHandler(BaseHandler):
    """Handle a request to /things/<thing>/events."""

    def get(self, thing_name):
        """
        Handle a GET request.

        thing_name -- the name of the thing from the URL path
        """
        pass


class WebThingServer:
    """Server to represent a Web Thing over HTTP."""

    def __init__(self, port=80):
        """
        Initialize the WebThingServer.

        port -- port to listen on (defaults to 80)
        """
        self.ip = get_ip()
        self.port = port
        self.things = {}

        self.app = tornado.web.Application([
            (
                r'/things/?',
                ThingsHandler,
                dict(things=self.things, ip=self.ip, port=self.port),
            ),
            (
                r'/things/([^/]+)/?',
                ThingHandler,
                dict(things=self.things, ip=self.ip, port=self.port),
            ),
            (
                r'/things/([^/]+)/properties/?',
                PropertiesHandler,
                dict(things=self.things, ip=self.ip, port=self.port),
            ),
            (
                r'/things/([^/]+)/properties/([^/]+)/?',
                PropertyHandler,
                dict(things=self.things, ip=self.ip, port=self.port),
            ),
            (
                r'/things/([^/]+)/actions/?',
                ActionsHandler,
                dict(things=self.things, ip=self.ip, port=self.port),
            ),
            (
                r'/things/([^/]+)/actions/([^/]+)/?',
                ActionHandler,
                dict(things=self.things, ip=self.ip, port=self.port),
            ),
            (
                r'/things/([^/]+)/events/?',
                EventsHandler,
                dict(things=self.things, ip=self.ip, port=self.port),
            ),
        ])

    def start(self):
        """Start listening for incoming connections."""
        self.app.listen(self.port)
        tornado.ioloop.IOLoop.current().start()

    def add_thing(self, thing):
        """
        Add a thing to the server.

        thing -- Thing to add
        """
        self.things[thing.name] = thing

    def remove_thing(self, thing):
        """
        Remove a thing from the server.

        thing -- Thing to remove
        """
        if thing.name in self.things:
            del self.things[thing.name]
