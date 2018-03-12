#!/bin/bash

python3 test-server.py &
SERVER_PID=$!

python3 test-client.py
CLIENT_RET=$?

kill -15 $SERVER_PID

exit $CLIENT_RET
