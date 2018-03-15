from queue import Queue
import json
import re
import time
import tornado.httpclient
import tornado.websocket
import websocket

from webthing.utils import get_ip


_TIME_REGEX = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$'


def http_request(method, path, data=None):
    url = 'http://127.0.0.1:8888' + path

    client = tornado.httpclient.HTTPClient()

    if data is None:
        request = tornado.httpclient.HTTPRequest(
            url,
            method=method,
            headers={
                'Accept': 'application/json',
            },
        )
    else:
        request = tornado.httpclient.HTTPRequest(
            url,
            method=method,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            body=json.dumps(data),
        )

    response = client.fetch(request, raise_error=False)

    if response.body:
        return response.code, json.loads(response.body)
    else:
        return response.code, None


def run_client():
    # Test thing description
    code, body = http_request('GET', '/')
    assert code == 200
    assert body['name'] == 'WoT Pi'
    assert body['type'] == 'thing'
    assert body['description'] == 'A WoT-connected Raspberry Pi'
    assert body['properties']['temperature']['type'] == 'number'
    assert body['properties']['temperature']['unit'] == 'celsius'
    assert body['properties']['temperature']['description'] == 'An ambient temperature sensor'
    assert body['properties']['temperature']['href'] == '/properties/temperature'
    assert body['properties']['humidity']['type'] == 'number'
    assert body['properties']['humidity']['unit'] == 'percent'
    assert body['properties']['humidity']['href'] == '/properties/humidity'
    assert body['properties']['led']['type'] == 'boolean'
    assert body['properties']['led']['description'] == 'A red LED'
    assert body['properties']['led']['href'] == '/properties/led'
    assert body['actions']['reboot']['description'] == 'Reboot the device'
    assert body['events']['reboot']['description'] == 'Going down for reboot'
    assert len(body['links']) == 4
    assert body['links'][0]['rel'] == 'properties'
    assert body['links'][0]['href'] == '/properties'
    assert body['links'][1]['rel'] == 'actions'
    assert body['links'][1]['href'] == '/actions'
    assert body['links'][2]['rel'] == 'events'
    assert body['links'][2]['href'] == '/events'
    assert body['links'][3]['rel'] == 'alternate'
    assert body['links'][3]['href'] == 'ws://{}:8888/'.format(get_ip())

    # Test properties
    code, body = http_request('GET', '/properties/temperature')
    assert code == 200
    assert body['temperature'] is None

    code, body = http_request('PUT', '/properties/temperature', {'temperature': 21})
    assert code == 200
    assert body['temperature'] == 21

    code, body = http_request('GET', '/properties/temperature')
    assert code == 200
    assert body['temperature'] == 21

    # Test events
    code, body = http_request('GET', '/events')
    assert code == 200
    assert len(body) == 0

    # Test actions
    code, body = http_request('GET', '/actions')
    assert code == 200
    assert len(body) == 0

    code, body = http_request('POST', '/actions', {'reboot': {}})
    assert code == 201
    assert body['reboot']['href'].startswith('/actions/')
    assert body['reboot']['status'] == 'created'
    action_id = body['reboot']['href'].split('/')[-1]
    time.sleep(.1)

    code, body = http_request('GET', '/actions')
    assert code == 200
    assert len(body) == 1
    assert len(body[0].keys()) == 1
    assert body[0]['reboot']['href'] == '/actions/reboot/' + action_id
    assert re.match(_TIME_REGEX, body[0]['reboot']['timeRequested']) is not None
    assert re.match(_TIME_REGEX, body[0]['reboot']['timeCompleted']) is not None
    assert body[0]['reboot']['status'] == 'completed'

    code, body = http_request('DELETE', '/actions/reboot/' + action_id)
    assert code == 204
    assert body is None

    # The action above generates an event, so check it.
    code, body = http_request('GET', '/events')
    assert code == 200
    assert len(body) == 1
    assert len(body[0].keys()) == 1
    assert body[0]['reboot']['description'] == 'Going down for reboot'
    assert re.match(_TIME_REGEX, body[0]['reboot']['time']) is not None

    # Set up a websocket
    ws = websocket.WebSocket()
    ws.connect('ws://127.0.0.1:8888/')

    # Test setting property through websocket
    ws.send(json.dumps({
        'messageType': 'setProperty',
        'data': {
            'temperature': 30,
        }
    }))
    message = json.loads(ws.recv())
    assert message['messageType'] == 'propertyStatus'
    assert message['data']['temperature'] == 30

    code, body = http_request('GET', '/properties/temperature')
    assert code == 200
    assert body['temperature'] == 30

    # Test requesting action through websocket
    ws.send(json.dumps({
        'messageType': 'requestAction',
        'data': {
            'reboot': {},
        }
    }))
    message = json.loads(ws.recv())
    assert message['messageType'] == 'actionStatus'
    assert message['data']['reboot']['href'].startswith('/actions/')
    assert message['data']['reboot']['status'] == 'created'
    message = json.loads(ws.recv())
    assert message['messageType'] == 'actionStatus'
    assert message['data']['reboot']['href'].startswith('/actions/')
    assert message['data']['reboot']['status'] == 'pending'
    message = json.loads(ws.recv())
    assert message['messageType'] == 'actionStatus'
    assert message['data']['reboot']['href'].startswith('/actions/')
    assert message['data']['reboot']['status'] == 'completed'
    action_id = message['data']['reboot']['href'].split('/')[-1]

    code, body = http_request('GET', '/actions')
    assert code == 200
    assert len(body) == 2
    assert len(body[1].keys()) == 1
    assert body[1]['reboot']['href'] == '/actions/reboot/' + action_id
    assert re.match(_TIME_REGEX, body[1]['reboot']['timeRequested']) is not None
    assert re.match(_TIME_REGEX, body[1]['reboot']['timeCompleted']) is not None
    assert body[1]['reboot']['status'] == 'completed'

    code, body = http_request('GET', '/actions/reboot/' + action_id)
    assert code == 200
    assert len(body.keys()) == 1
    assert body['reboot']['href'] == '/actions/reboot/' + action_id
    assert re.match(_TIME_REGEX, body['reboot']['timeRequested']) is not None
    assert re.match(_TIME_REGEX, body['reboot']['timeCompleted']) is not None
    assert body['reboot']['status'] == 'completed'

    code, body = http_request('GET', '/events')
    assert code == 200
    assert len(body) == 2
    assert len(body[1].keys()) == 1
    assert body[1]['reboot']['description'] == 'Going down for reboot'
    assert re.match(_TIME_REGEX, body[1]['reboot']['time']) is not None

    # Test event subscription through websocket
    ws.send(json.dumps({
        'messageType': 'addEventSubscription',
        'data': {
            'reboot': {},
        }
    }))
    ws.send(json.dumps({
        'messageType': 'requestAction',
        'data': {
            'reboot': {},
        }
    }))
    message = json.loads(ws.recv())
    assert message['messageType'] == 'actionStatus'
    assert message['data']['reboot']['href'].startswith('/actions/')
    assert message['data']['reboot']['status'] == 'created'
    assert re.match(_TIME_REGEX, message['data']['reboot']['timeRequested']) is not None
    message = json.loads(ws.recv())
    assert message['messageType'] == 'actionStatus'
    assert message['data']['reboot']['href'].startswith('/actions/')
    assert message['data']['reboot']['status'] == 'pending'
    assert re.match(_TIME_REGEX, message['data']['reboot']['timeRequested']) is not None
    message = json.loads(ws.recv())
    assert message['messageType'] == 'event'
    assert re.match(_TIME_REGEX, message['data']['reboot']['timestamp']) is not None
    message = json.loads(ws.recv())
    assert message['messageType'] == 'actionStatus'
    assert message['data']['reboot']['href'].startswith('/actions/')
    assert message['data']['reboot']['status'] == 'completed'
    assert re.match(_TIME_REGEX, message['data']['reboot']['timeRequested']) is not None
    assert re.match(_TIME_REGEX, message['data']['reboot']['timeCompleted']) is not None

    ws.close()


if __name__ == '__main__':
    exit(run_client())
