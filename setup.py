"""A setuptools based setup module."""

from setuptools import setup, find_packages
from codecs import open
from os import path
import sys


here = path.abspath(path.dirname(__file__))

# Get the long description from the README file.
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='webthing',
    version='0.15.0',
    description='HTTP Web Thing implementation',
    long_description=long_description,
    url='https://github.com/WebThingsIO/webthing-python',
    author='WebThingsIO',
    author_email='team@webthings.io',
    keywords='iot web thing webthing',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=[
        'ifaddr>=0.1.0',
        'jsonschema>=3.2.0',
        'pyee>=8.1.0',
        'tornado>=6.1.0',
        'zeroconf>=0.28.0',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    license='MPL-2.0',
    project_urls={
        'Source': 'https://github.com/WebThingsIO/webthing-python',
        'Tracker': 'https://github.com/WebThingsIO/webthing-python/issues',
    },
    python_requires='>=3.5, <4',
)
