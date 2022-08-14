import pytest

from fxtrade import stock

from fractions import Fraction
from fxtrade.stock import Stock, Rate

### class Stock ###

def test_stock_helpers():
    assert stock.can_be_precise_num(3)
    assert stock.can_be_precise_num(0.3)
    assert stock.can_be_precise_num('0.3')
    assert stock.can_be_precise_num(Fraction('0.3'))

    with pytest.warns(UserWarning):
        assert not stock.can_be_precise_num(0.313131313131)
    
    assert stock.as_numeric(3) == Fraction(3)
    
    with pytest.raises(TypeError):
        stock.as_numeric([1, 2])

def test_init():
    x1 = Stock('BTC', 15)
    x2 = Stock('BTC', '1/6')
    x3 = Stock('BTC', Fraction('1/3'))

    assert x1.__repr__() == 'Stock(BTC, 15)'
    
    assert x1.q == Fraction('15')
    assert x2.q == Fraction('1/6')
    assert x3.q == Fraction('1/3')
    
    with pytest.raises(TypeError):
        Stock(3, 4)

    with pytest.warns(UserWarning):
        with pytest.raises(TypeError):
            x4 = Stock('BTC', 0.0031313131)
    
    
def test_q():
    x = Stock('BTC', 15)
    
    with pytest.raises(AttributeError):
        x.q = 5

def test_floor_and_ceil():
    x = Stock('BTC', '0.0314159')

    assert x.floor(3) == Stock('BTC', '0.031')
    assert x.ceil(4) == Stock('BTC', '0.0315')

def test_comparison_operators():
    x = Stock('BTC', 2)
    y = Stock('BTC', 3)
    z = Stock('BTC', 2)
    w = Stock('BTC', 1)
    
    v = Stock('JPY', 2)
    
    assert x < y
    assert x <= y
    assert x <= z
    assert x == z
    assert x != y
    assert x > w
    assert x >= w
    assert x >= z

    assert x < 3
    assert x <= 3
    assert x <= 2
    assert x == 2
    assert x != 3
    assert x > 1
    assert x >= 1
    assert x >= 2
    
    assert not (x < w)
    assert not (x <= w)
    assert not (x == y)
    assert not (x != z)
    assert not (x > y)
    assert not (x >= y)
    
    with pytest.raises(TypeError):
        assert x < v
    with pytest.raises(TypeError):
        assert x <= v
    with pytest.raises(TypeError):
        assert x <= v
    with pytest.raises(TypeError):
        assert x == v
    with pytest.raises(TypeError):
        assert x != v
    with pytest.raises(TypeError):
        assert x > v
    with pytest.raises(TypeError):
        assert x >= v
    with pytest.raises(TypeError):
        assert x >= v

def test_unary_operators():
    x = Stock('BTC', -2)
    
    assert abs(x) == Stock('BTC', 2)
    assert +x == Stock('BTC', -2)
    assert -x == Stock('BTC', 2)

def test_binary_operators():
    x = Stock('BTC', 3)
    y = Stock('BTC', 2)
    z = Stock('JPY', 100)
    a = Fraction('1/3')
    b = Fraction(2)
    
    assert x + y == Stock('BTC', 5)
    assert x + b == Stock('BTC', 5)
    assert b + x == Stock('BTC', 5)
    assert x - y == Stock('BTC', 1)
    assert x - b == Stock('BTC', 1)
    assert b - x == Stock('BTC', -1)
    
    assert x * a == Stock('BTC', 1)
    assert a * x == Stock('BTC', 1)
    
    assert x / a == Stock('BTC', 9)
    assert x // a == Stock('BTC', 9)
    assert x % a == Stock('BTC', 0)
    
    assert x ** 3 == Stock('BTC', 27)
    
    with pytest.raises(TypeError):
        x + z
    with pytest.raises(TypeError):
        x - z
    with pytest.raises(TypeError):
        x * y
    with pytest.raises(TypeError):
        x * z
    with pytest.raises(TypeError):
        x / y
    with pytest.raises(TypeError):
        x / z

### class Rate ###

def test_init():
    r1 = Rate('JPY', 'BTC', '1/3')
    r2 = Rate.from_stocks(Stock('JPY', 3), Stock('BTC', 1))
    
    assert r1.r == Fraction('1/3')
    assert r2.from_code == 'JPY'
    assert r2.to_code == 'BTC'

    with pytest.raises(TypeError):
        Rate.from_stocks(3, 4)
    
    with pytest.raises(TypeError):
        Rate(3, 4, 5)
    
    with pytest.raises(TypeError):
        Rate('JPY', 4, 5)
    
def test_equal():
    r1 = Rate('JPY', 'BTC', '1/3')
    r2 = Rate.from_stocks(Stock('JPY', 3), Stock('BTC', 1))
    r3 = Rate.from_stocks(Stock('JPY', 2), Stock('BTC', 1))
    r4 = Rate.from_stocks(Stock('USD', 3), Stock('BTC', 1))
    r5 = 5
    
    assert r1 == r2
    assert r1 != r3
    assert r1 != r4
    
    assert not (r1 == r3)
    assert not (r1 == r4)
    assert not (r1 != r2)
    
    with pytest.raises(TypeError):
        r1 == r5
        
def test_unary_operators():
    r1 = Rate('JPY', 'BTC', '1/3')
    r2 = Rate('BTC', 'JPY', '3')
    
    assert ~r1 == r2

def test_binary_operators():
    r1 = Rate('JPY', 'BTC', '1/3')
    r2 = Rate('BTC', 'JPY', '6')
    r3 = Rate('JPY', 'JPY', 2)
    r4 = Rate('JPY', 'JPY', 8)
    r5 = Rate('JPY', 'BTC', 2)
    
    x1 = Stock('JPY', 300)
    x2 = Stock('BTC', 100)
    x3 = Stock('JPY', 50)
    
    assert r1 * r2 == r3
    assert r3 ** 3 == r4
    
    assert r1 * 6 == r5
    assert 6 * r1 == r5
    
    assert r1 * x1 == x2
    assert x1 * r1 == x2
    
    assert 2 / r1 == r2
    assert x2 / r5 == x3
    
    with pytest.raises(TypeError):
        r1 * r3
    with pytest.raises(TypeError):
        r1 ** r2
    with pytest.raises(TypeError):
        6 ** r2