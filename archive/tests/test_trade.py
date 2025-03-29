import pytest

import pandas as pd

from fractions import Fraction

from fxtrade.stock import Stock, Rate
from fxtrade.stocks import JPY, BTC
from fxtrade.trade import Trade

def test_init():
    x = JPY(20000)
    y = BTC('0.005')
    
    t = Trade(x, y)
    
    assert t.rate == Rate.from_stocks(x, y)

def test_split():
    x1 = JPY(20000)
    y1 = BTC('0.005')
    
    x2 = JPY(5000)
    y2 = BTC('0.003')
    
    t = Trade(x1, y1)
    
    z1, z2 = t.split(x2)
    z3, z4 = t.split(y2)
    
    assert z1.x == x2
    assert z2.x == JPY(15000)
    assert z1.y == BTC('0.00125')
    assert z2.y == BTC('0.00375')
    
    assert z3.x == JPY(12000)
    assert z4.x == JPY(8000)
    assert z3.y == y2
    assert z4.y == BTC('0.002')
    
    x3 = JPY(30000)
    y3 = BTC('0.006')
    a3 = Stock('USD', 2000)
    
    with pytest.raises(ValueError):
        t.split(x3)
    with pytest.raises(ValueError):
        t.split(y3)
    with pytest.raises(TypeError):
        t.split(a3)
    
    with pytest.raises(ValueError):
        t.split_x(x3)
    with pytest.raises(ValueError):
        t.split_y(y3)
    with pytest.raises(TypeError):
        t.split_x(a3)
    with pytest.raises(TypeError):
        t.split_y(a3)

def test_settle():
    x = JPY(20000)
    y = BTC('0.005')
    z = JPY(21000)
    
    y1 = BTC('0.004')
    y2 = BTC('0.006')
    
    t1 = Trade(x, y, t=pd.Timestamp(2022, 4, 1))
    
    t2 = Trade(y, z, t=pd.Timestamp(2022, 4, 2))
    t3 = Trade(y1, z, t=pd.Timestamp(2022, 4, 2))
    t4 = Trade(y2, z, t=pd.Timestamp(2022, 4, 2))
    
    t5 = Trade(y, z, t=pd.Timestamp(2022, 3, 1))
    
    tp, unsettled = t1.settle(t2)
    assert unsettled is None
    
    tp, unsettled = t1.settle(t3)
    assert unsettled.y == BTC('0.001')
    
    tp, unsettled = t1.settle(t4)
    assert unsettled.x == BTC('0.001')
    
    with pytest.raises(ValueError):
        t1.settle(t5)
