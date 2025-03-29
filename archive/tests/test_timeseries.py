import pytest

from datetime import datetime

from fxtrade.timeseries import get_first_timestamp

def test_delta():
    pass

def test_get_first_timestamp():
    t = datetime(2023, 3, 14, 15, 9, 26)

    assert get_first_timestamp(t, '1d') == datetime(2023, 3, 14)
    assert get_first_timestamp(t, '24h') == datetime(2023, 3, 14)
    assert get_first_timestamp(t, '12h') == datetime(2023, 3, 14, 12)
    assert get_first_timestamp(t, '6h') == datetime(2023, 3, 14, 12)
    assert get_first_timestamp(t, '3h') == datetime(2023, 3, 14, 15)
    assert get_first_timestamp(t, '2h') == datetime(2023, 3, 14, 14)
    assert get_first_timestamp(t, '1h') == datetime(2023, 3, 14, 15)
    assert get_first_timestamp(t, '60m') == datetime(2023, 3, 14, 15)
    assert get_first_timestamp(t, '30m') == datetime(2023, 3, 14, 15)
    assert get_first_timestamp(t, '20m') == datetime(2023, 3, 14, 15)
    assert get_first_timestamp(t, '15m') == datetime(2023, 3, 14, 15)
    assert get_first_timestamp(t, '10m') == datetime(2023, 3, 14, 15)
    assert get_first_timestamp(t, '5m') == datetime(2023, 3, 14, 15, 5)
    assert get_first_timestamp(t, '1m') == datetime(2023, 3, 14, 15, 9)
    assert get_first_timestamp(t, '60s') == datetime(2023, 3, 14, 15, 9)
    assert get_first_timestamp(t, '30s') == datetime(2023, 3, 14, 15, 9)
    assert get_first_timestamp(t, '20s') == datetime(2023, 3, 14, 15, 9, 20)
    assert get_first_timestamp(t, '15s') == datetime(2023, 3, 14, 15, 9, 15)
    assert get_first_timestamp(t, '10s') == datetime(2023, 3, 14, 15, 9, 20)
    assert get_first_timestamp(t, '5s') == datetime(2023, 3, 14, 15, 9, 25)
    assert get_first_timestamp(t, '1s') == datetime(2023, 3, 14, 15, 9, 26)