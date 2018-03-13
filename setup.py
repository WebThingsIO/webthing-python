"""A setuptools based setup module."""

from setuptools import setup, find_packages
from codecs import open
from os import path


here = path.abspath(path.dirname(__file__))

# Get the long description from the README file.
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='webthing',
    version='0.2.0',
    description='HTTP Web Thing implementation',
    long_description=long_description,
    url='https://github.com/mozilla-iot/webthing-python',
    author='Michael Stegeman',
    author_email='mrstegeman@gmail.com',
    keywords='mozilla iot web thing webthing',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=['tornado', 'zeroconf'],
)
