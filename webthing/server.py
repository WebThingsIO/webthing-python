"""Python Web Thing server implementation."""

import json
import tornado.concurrent
import tornado.gen
import tornado.ioloop
import tornado.web
import tornado.websocket

from .utils import get_ip


@tornado.gen.coroutine
def perform_action(action):
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
        self.ws_path = 'ws://{}:{}/'.format(ip, port)

    @tornado.web.asynchronous
    def get(self, *args, **kwargs):
        """Handle a GET request."""
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
                action = self.thing.perform_action(action_name,
                                                   **action_params)
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
            self.set_status(200)
        else:
            self.set_status(404)


class ActionsHandler(BaseHandler):
    """Handle a request to /actions."""

    def get(self):
        """Handle a GET request."""
        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps([a.as_action_description()
                               for a in self.thing.actions]))

    def post(self):
        """Handle a POST request."""
        try:
            message = json.loads(self.request.body)
        except ValueError:
            self.set_status(400)
            return

        if 'name' not in message or \
                message['name'] not in self.thing.available_actions:
            self.set_status(400)
            return

        params = message['data'] if 'data' in message else {}
        action = self.thing.perform_action(message['name'], **params)
        self.set_status(201)
        self.write(json.dumps({
            'name': action.name,
            'href': action.href,
        }))

        # Start the action
        tornado.ioloop.IOLoop.current().spawn_callback(perform_action, action)


class ActionHandler(BaseHandler):
    """Handle a request to /actions/<action>."""

    def get(self, action_id):
        """
        Handle a GET request.

        action_id -- the action ID from the URL path
        """
        for action in self.thing.actions:
            if action.id == action_id:
                self.set_header('Content-Type', 'application/json')
                self.write(json.dumps(action.as_action_description()))
                return

        self.set_status(404)

    def put(self, action_id):
        """
        Handle a PUT request.

        TODO: this is not yet defined in the spec

        action_id -- the action ID from the URL path
        """
        pass

    def delete(self, action_id):
        """
        Handle a DELETE request.

        action_id -- the action ID from the URL path
        """
        for action in self.thing.actions:
            if action.id == action_id:
                action.cancel()
                self.set_status(204)
                return

        self.set_status(404)


class EventsHandler(BaseHandler):
    """Handle a request to /events."""

    def get(self):
        """Handle a GET request."""
        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps([e.as_event_description()
                               for e in self.thing.events]))


class WebThingServer:
    """Server to represent a Web Thing over HTTP."""

    def __init__(self, thing, port=80):
        """
        Initialize the WebThingServer.

        thing -- the Thing managed by this server
        port -- port to listen on (defaults to 80)
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
                r'/events/?',
                EventsHandler,
                dict(thing=self.thing),
            ),
        ])

    def start(self):
        """Start listening for incoming connections."""
        self.app.listen(self.port)
        tornado.ioloop.IOLoop.current().start()
