import pytest

from datetime import timedelta

from fxtrade.period import to_seconds, to_period_str, is_divisor, Period, CRange, CRangePeriod

def test_to_seconds():
    assert to_seconds('max') == -1
    assert to_seconds('1h') == 3600

    assert to_seconds(0, 'max') == -1
    assert to_seconds(-1, 'max') == -1
    assert to_seconds(-5, 'Max') == -1
    assert to_seconds(10, 'MAX') == -1

    assert to_seconds('2', 's') == 2
    assert to_seconds(3, 'm') == 180
    assert to_seconds(1, 'h') == 3600

    assert to_seconds('1mo') == -1
    assert to_seconds(1, 'mo') == -1

    with pytest.raises(ValueError):
        to_seconds(-1, 's')

def test_to_period_str():
    assert to_period_str(timedelta(days=15)) == '15d'
    assert to_period_str(timedelta(days=1)) == '1d'
    assert to_period_str(timedelta(hours=12)) == '12h'
    assert to_period_str(timedelta(hours=6)) == '6h'
    assert to_period_str(timedelta(minutes=30)) == '30m'
    assert to_period_str(timedelta(minutes=1)) == '1m'
    assert to_period_str(timedelta(seconds=20)) == '20s'
    assert to_period_str(timedelta(seconds=1)) == '1s'

    with pytest.raises(ValueError):
        to_period_str(timedelta(0))

def test_is_divisor():
    assert is_divisor('1d')
    assert is_divisor('24h')
    assert is_divisor('12h')
    assert is_divisor('1h')
    assert is_divisor('60m')
    assert is_divisor('15s')
    assert is_divisor('5s')

    assert not is_divisor('2d')
    assert not is_divisor('15h')
    assert not is_divisor('45m')
    assert not is_divisor('40s')

def test_Period():
    assert Period('max') == -1
    assert Period('1h') == 3600
    assert Period('max') < Period('1h')
    assert Period('1h') > Period('1m')

    assert Period(Period('1h')) == 3600

    with pytest.raises(TypeError):
        assert Period('max') == 'hoge'

def test_CRange():
    assert CRange('max') == -1
    assert CRange('1h') == 3600
    assert CRange('max') < CRange('1h')
    assert CRange('1h') > CRange('1m')
    assert CRange('max') < Period('1h')
    assert CRange('1h') > Period('1m')

    assert CRange(CRange('1h')) == 3600

    with pytest.raises(TypeError):
        assert CRange('max') == 'hoge'

def test_CRangePeriod():
    assert CRangePeriod('max', '1m') == CRangePeriod('max', '1m')
    assert CRangePeriod('max', '1m') != CRangePeriod('max', '15m')
    assert CRangePeriod('max', '1m') < CRangePeriod('max', '15m')

    assert CRangePeriod('1mo', '15m').short == '1mo-15m'

    with pytest.raises(ValueError):
        CRangePeriod('max', 'xxx')
    
    xs = {}
    xs[CRangePeriod('max', '1m')] = 5
    assert xs[CRangePeriod('max', '1m')] == 5