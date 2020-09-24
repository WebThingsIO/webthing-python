"""
    JSON Web Token auth for Tornado
    Modified by marc at m2ag-labs (marc@m2ag.net) from files found here:
    https://github.com/paulorodriguesxv/tornado-json-web-token-jwt
    by Codekraft - Paulo Rodrigues
    Added configuration from file, errors as dict, added a check for
    websocket upgrade (wss add auth parameter to connect string -- ?Authorization=Bearer <token>)
"""
import jwt
import json
from pathlib import Path

# TODO: move to where? secret key in config
AUTHORIZATION_HEADER = 'Authorization'
AUTHORIZATION_METHOD = 'bearer'
INVALID_HEADER_MESSAGE = {"error": "invalid header authorization"}
MISSING_AUTHORIZATION_KEY = {"error": "missing authorization"}
AUTHORIZTION_ERROR_CODE = 401
ENABLE = False
SECRET_KEY = ''

# secret can be any string
# enable false will bypass auth checks
'''{
    "secret":  "01q2387oiafo6e978q2365-82q3",
    "enable":  true
} '''
try:
    with open(f'{str(Path.home())}/.m2ag-labs/secrets/jwt_secret.json', 'r') as file:
        opts = json.loads(file.read().replace('\n', ''))
        for i in opts:
            if i == 'secret':
                SECRET_KEY = opts[i]
            if i == 'enable':
                ENABLE = opts[i]
except FileNotFoundError:
    pass  # go with defaults if no file found -- disable.


jwt_options = {
    'verify_signature': True,
    'verify_exp': True,
    'verify_nbf': False,
    'verify_iat': True,
    'verify_aud': False
}


def is_valid_header(parts):
    """
        Validate the header
    """
    if parts[0].lower() != AUTHORIZATION_METHOD:
        return False
    elif len(parts) == 1:
        return False
    elif len(parts) > 2:
        return False

    return True


def return_auth_error(handler, message):
    """
        Return authorization error 
    """
    handler._transforms = []
    handler.set_status(AUTHORIZTION_ERROR_CODE)
    handler.write(message)
    handler.finish()


def return_header_error(handler):
    """
        Returh authorization header error
    """
    return_auth_error(handler, INVALID_HEADER_MESSAGE)


def jwtauth(handler_class):
    """
        Tornado JWT Auth Decorator
    """

    def wrap_execute(handler_execute):
        def require_auth(handler, kwargs):
            # configure the jwt with a config file
            if not ENABLE:
                return True

            auth = handler.request.headers.get(AUTHORIZATION_HEADER)
            if auth:
                parts = auth.split()

                if not is_valid_header(parts):
                    return_header_error(handler)

                token = parts[1]
                try:
                    jwt.decode(
                        token,
                        SECRET_KEY,
                        options=jwt_options
                    )
                except Exception as err:
                    return_auth_error(handler, str(err))

            else:
                # is this websocket upgrade? if so look for auth header in params
                upgrade = handler.request.headers.get("Upgrade")
                if upgrade == 'websocket':
                    auth = handler.request.query_arguments.get(AUTHORIZATION_HEADER)[0].decode('UTF-8')
                    if auth:
                        parts = auth.split()

                        if not is_valid_header(parts):
                            return_header_error(handler)

                        token = parts[1]
                        try:
                            jwt.decode(
                                token,
                                SECRET_KEY,
                                options=jwt_options
                            )
                        except Exception as err:
                            return_auth_error(handler, str(err))
                        return True
                handler._transforms = []
                handler.write(MISSING_AUTHORIZATION_KEY)
                handler.finish()

            return True

        def _execute(self, transforms, *args, **kwargs):

            try:
                require_auth(self, kwargs)
            except Exception:
                return False

            return handler_execute(self, transforms, *args, **kwargs)

        return _execute

    handler_class._execute = wrap_execute(handler_class._execute)
    return handler_class
