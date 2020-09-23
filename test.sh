#!/bin/bash -e

# run flake8 and pydocstyle
pip install flake8 pydocstyle
flake8 webthing
pydocstyle webthing

# clone the webthing-tester
git clone https://github.com/WebThingsIO/webthing-tester
pip install -r webthing-tester/requirements.txt

# build and test the single-thing example
PYTHONPATH=. python example/single-thing.py &
EXAMPLE_PID=$!
sleep 5
python ./webthing-tester/test-client.py
kill -15 $EXAMPLE_PID

# build and test the multiple-things example
PYTHONPATH=. python example/multiple-things.py &
EXAMPLE_PID=$!
sleep 5
python ./webthing-tester/test-client.py --path-prefix "/0"
kill -15 $EXAMPLE_PID
