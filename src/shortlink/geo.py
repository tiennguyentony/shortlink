"""Country lookup for click analytics.

Production would use a MaxMind database. Until then we use a small offline
table keyed on the first octet of an IPv4 address, which is good enough for
the demo and fully deterministic in tests.
"""

import ipaddress
from typing import Protocol

UNKNOWN_COUNTRY = "ZZ"

_FIRST_OCTET = {
    3: "US", 8: "US", 24: "US", 66: "US", 73: "US",
    2: "FR", 31: "NL", 46: "SE", 51: "GB", 81: "GB", 86: "GB",
    62: "DE", 88: "DE", 93: "ES", 95: "IT",
    1: "AU", 49: "JP", 58: "CN", 101: "IN", 103: "SG", 203: "AU",
    177: "BR", 189: "MX", 41: "ZA", 99: "CA", 142: "CA",
}


class GeoLookup(Protocol):
    def country_for(self, ip: str | None) -> str: ...


class OfflineGeo:
    def country_for(self, ip: str | None) -> str:
        if not ip:
            return UNKNOWN_COUNTRY
        try:
            address = ipaddress.ip_address(ip)
        except ValueError:
            return UNKNOWN_COUNTRY
        if address.version != 4 or address.is_private or address.is_loopback:
            return UNKNOWN_COUNTRY
        first_octet = int(str(address).split(".")[0])
        return _FIRST_OCTET.get(first_octet, UNKNOWN_COUNTRY)
