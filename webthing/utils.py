"""Utility functions."""

import datetime
import netifaces
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


def get_addresses():
    """
    Get all IP addresses.

    Returns list of addresses.
    """
    addresses = set()

    for iface in netifaces.interfaces():
        for family, addrs in netifaces.ifaddresses(iface).items():
            if family not in [netifaces.AF_INET, netifaces.AF_INET6]:
                continue

            # Sometimes, IPv6 addresses will have the interface name appended
            # as, e.g. %eth0. Handle that.
            for addr in [a['addr'].split('%')[0].lower() for a in addrs]:
                # Filter out link-local addresses.
                if family == netifaces.AF_INET and \
                        not addr.startswith('169.254.'):
                    addresses.add(addr)
                elif family == netifaces.AF_INET6 and \
                        not addr.startswith('fe80:'):
                    addresses.add('[{}]'.format(addr))

    return sorted(list(addresses))
