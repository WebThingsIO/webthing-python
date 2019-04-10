"""Utility functions."""

import datetime
import ifaddr
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

    for iface in ifaddr.get_adapters():
        for addr in iface.ips:
            # Filter out link-local addresses.
            if addr.is_IPv4:
                ip = addr.ip

                if not ip.startswith('169.254.'):
                    addresses.add(ip)
            elif addr.is_IPv6:
                # Sometimes, IPv6 addresses will have the interface name
                # appended, e.g. %eth0. Handle that.
                ip = addr.ip[0].split('%')[0].lower()

                if not ip.startswith('fe80:'):
                    addresses.add('[{}]'.format(ip))

    return sorted(list(addresses))
