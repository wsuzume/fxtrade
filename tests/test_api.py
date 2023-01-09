import pytest

from fxtrade.api import CodePair, CrangePeriod

def test_CodePair():
    codepair = CodePair('BTC', 'JPY')
    
    assert codepair.base == 'BTC'
    assert codepair.quote == 'JPY'

    codepair2 = codepair.copy()

    assert codepair2.base == 'BTC'
    assert codepair2.quote == 'JPY'

def test_CrangePeriod():
    crange_period = CrangePeriod('max', '15m')

    assert crange_period == CrangePeriod('max', '15m')
    assert crange_period != CrangePeriod('max', '1m')