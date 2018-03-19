#!/bin/bash

rm -rf build/ dist/

cp requirements-py2.txt requirements.txt
python setup.py bdist_wheel

cp requirements-py3.txt requirements.txt
python3.6 setup.py bdist_wheel

python3.6 setup.py sdist

rm -f requirements.txt
