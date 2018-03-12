#!/bin/bash

python3 test-server.py &
SERVER_PID=$!

python3 test-client.py
CLIENT_RET=$?

kill -15 $SERVER_PID

if [ $CLIENT_RET -eq 0 ]; then
    echo Pass
else
    echo Fail
fi

exit $CLIENT_RET
