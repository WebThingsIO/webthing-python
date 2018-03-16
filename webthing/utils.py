"""Utility functions."""

import datetime
import socket


def timestamp():
    """
    Get the current time.

    Returns the current time in the form YYYY-mm-ddTHH:MM:SS+00:00
    """
    return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S+00:00')


def get_ip():
    """
    Get the default local IP address.

    From: https://stackoverflow.com/a/28950776
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except (socket.error, IndexError):
        ip = '127.0.0.1'
    finally:
        s.close()

    return ip
