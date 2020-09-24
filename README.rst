webthing
========


Implementation of an HTTP `Web Thing <https://iot.mozilla.org/wot/>`_. This library is compatible with Python 2.7 and 3.5+.

m2ag-labs fork:
===============
- Adds support for jwt authentication on restful and websocket access.
- Configuration is expectect in $HOME/.m2ag-labs/secrets/jwt_secret.json



    {
       "secret":  "01q2387oiafo6e978q2365-82q3",
        "enable":  true

    }

- Secret is shared with auth api to generate jwt
- If enable set to false jwts will not be checked.
- Server must be restarted if config changed.
- Generate tokens with code similar to `this <https://github.com/m2ag-labs/m2ag-thing/blob/master/api/helpers/auth.py>`_


Installation
============
First - uninstall webthing python if already installed

.. code:: shell

  $ pip3 uninstall webthing


Then - ``webthing`` fork must be installed via ``git``, as such:


.. code:: shell

  $ git clone https://github.com/m2ag-labs/webthing-python.git

Running the Sample
==================

Please see the `source repo <https://github.com/WebThingsIO/webthing-python>`_ for instructions on the sample.

Credits
=======
`jwt code based on work by Paulo Rodrigues <https://github.com/paulorodriguesxv/tornado-json-web-token-jwt>`_