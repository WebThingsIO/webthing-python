"""A setuptools based setup module."""

from setuptools import setup, find_packages
from codecs import open
from os import path
import sys


here = path.abspath(path.dirname(__file__))

# Get the long description from the README file.
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

if sys.version_info.major == 2:
    requirements = ['tornado', 'zeroconf==0.19.1']
else:
    requirements = ['tornado', 'zeroconf']

setup(
    name='webthing',
    version='0.4.0',
    description='HTTP Web Thing implementation',
    long_description=long_description,
    url='https://github.com/mozilla-iot/webthing-python',
    author='Mozilla IoT',
    author_email='iot@mozilla.com',
    keywords='mozilla iot web thing webthing',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=requirements,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    license='MPL-2.0',
    project_urls={
        'Source': 'https://github.com/mozilla-iot/webthing-python',
        'Tracker': 'https://github.com/mozilla-iot/webthing-python/issues',
    },
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, <4',
)
