import pytest

from fxtrade.api import CRangePeriod

def test_CRangePeriod():
    crange_period = CRangePeriod('max', '15m')

    assert crange_period == CRangePeriod('max', '15m')
    assert crange_period != CRangePeriod('max', '1m')