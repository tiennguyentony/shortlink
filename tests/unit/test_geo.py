import pytest

from shortlink.geo import UNKNOWN_COUNTRY, OfflineGeo


@pytest.mark.parametrize(
    "ip, country",
    [
        ("81.2.69.160", "GB"),
        ("24.48.0.1", "US"),
        ("203.12.160.35", "AU"),
        ("10.0.0.1", UNKNOWN_COUNTRY),
        ("127.0.0.1", UNKNOWN_COUNTRY),
        ("2001:db8::1", UNKNOWN_COUNTRY),
        ("testclient", UNKNOWN_COUNTRY),
        (None, UNKNOWN_COUNTRY),
    ],
)
def test_country_for(ip, country):
    assert OfflineGeo().country_for(ip) == country
