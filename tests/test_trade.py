import pytest

import pandas as pd

from fractions import Fraction

from fxtrade.stock import Stock, Rate
from fxtrade.stocks import JPY, BTC
from fxtrade.trade import Trade, History

### class Trade ###

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

### class History ###

def test_init():
    hist = History()
    
    assert len(hist.df) == 0

def test_functions():
    trade = Trade(x=JPY('25000'), y=BTC('0.006'), order_id='JOR90623343')
    
    buys = [
        Trade(x=JPY('20000'), y=BTC('0.006'), order_id='JOR111111', t=pd.Timestamp(2022, 4, 1)),
        Trade(x=JPY('25000'), y=BTC('0.005'), order_id='JOR222222', t=pd.Timestamp(2022, 4, 3)),
        Trade(x=JPY('22000'), y=BTC('0.002'), order_id='JOR333333', t=pd.Timestamp(2022, 4, 4)),
        Trade(x=JPY('23000'), y=BTC('0.007'), order_id='JOR444444', t=pd.Timestamp(2022, 4, 6)),
        Trade(x=JPY('24000'), y=BTC('0.003'), order_id='JOR555555', t=pd.Timestamp(2022, 4, 8)),
    ]

    sells = [
        Trade(y=JPY('21000'), x=BTC('0.006'), order_id='JOR666666', t=pd.Timestamp(2022, 4, 2)),
        Trade(y=JPY('26000'), x=BTC('0.005'), order_id='JOR777777', t=pd.Timestamp(2022, 4, 5)),
        Trade(y=JPY('22000'), x=BTC('0.002'), order_id='JOR888888', t=pd.Timestamp(2022, 4, 6)),
        Trade(y=JPY('28000'), x=BTC('0.007'), order_id='JOR999999', t=pd.Timestamp(2022, 4, 7)),
        Trade(y=JPY('21000'), x=BTC('0.003'), order_id='JOR000000', t=pd.Timestamp(2022, 4, 9)),
    ]

    all_trades = sorted(buys + sells, key=lambda x: x.t)
    
    hist = History()
    hist.add(trade)
    
    assert len(hist.df) == 1
    
    hist.add(all_trades)
    
    assert len(hist.df) == 11
    
    hist.drop([0, 1, 2])
    
    assert len(hist.df) == 8
    
    ts = hist.as_trade_list()
    
    assert len(ts) == 8

def test_get_pair_trade_index():
    buys = [
        Trade(x=JPY('20000'), y=BTC('0.006'), order_id='JOR111111', t=pd.Timestamp(2022, 4, 1)),
        Trade(x=JPY('25000'), y=BTC('0.006'), order_id='JOR222222', t=pd.Timestamp(2022, 4, 2)),
        Trade(x=JPY('23000'), y=BTC('0.006'), order_id='JOR333333', t=pd.Timestamp(2022, 4, 3)),
    ]

    sells = [
        Trade(x=BTC('0.005'), y=JPY('20000'), order_id='JOR444444', t=pd.Timestamp(2022, 4, 4)),
        Trade(x=BTC('0.007'), y=JPY('20000'), order_id='JOR555555', t=pd.Timestamp(2022, 4, 5)),
        Trade(x=BTC('0.006'), y=JPY('20000'), order_id='JOR666666', t=pd.Timestamp(2022, 4, 6)),
    ]

    all_trades = sorted(buys + sells, key=lambda x: x.t)
    
    # ぴったり同額
    t1 = Trade(x=BTC('0.006'), y=JPY('25000'), order_id='JOR777777', t=pd.Timestamp(2022, 4, 7))
    # 少しだけ売る
    t2 = Trade(x=BTC('0.004'), y=JPY('25000'), order_id='JOR777777', t=pd.Timestamp(2022, 4, 7))
    # 1回に買った量より多く売る
    t3 = Trade(x=BTC('0.008'), y=JPY('25000'), order_id='JOR777777', t=pd.Timestamp(2022, 4, 7))
    # 持ってる全額より多く売る
    t4 = Trade(x=BTC('0.020'), y=JPY('25000'), order_id='JOR777777', t=pd.Timestamp(2022, 4, 7))
    
    # ぴったり同額
    t5 = Trade(x=JPY('20000'), y=BTC('0.006'), order_id='JOR777777', t=pd.Timestamp(2022, 4, 7))
    # 少しだけ売る
    t6 = Trade(x=JPY('15000'), y=BTC('0.006'), order_id='JOR777777', t=pd.Timestamp(2022, 4, 7))
    # 1回に買った量より多く売る
    t7 = Trade(x=JPY('25000'), y=BTC('0.006'), order_id='JOR777777', t=pd.Timestamp(2022, 4, 7))
    # 持ってる全額より多く売る
    t8 = Trade(x=JPY('80000'), y=BTC('0.006'), order_id='JOR777777', t=pd.Timestamp(2022, 4, 7))
    
    
    hist = History(all_trades)
    
    idx = hist.get_pair_trade_index(t1)
    assert idx[0] == 1
    idx = hist.get_pair_trade_index(t2)
    assert idx[0] == 1
    idx = hist.get_pair_trade_index(t3)
    assert idx[0] == 1
    assert idx[1] == 2
    idx = hist.get_pair_trade_index(t4)
    assert idx[0] == 1
    assert idx[1] == 2
    assert idx[2] == 0
    
    idx = hist.get_pair_trade_index(t5)
    assert idx[0] == 4
    idx = hist.get_pair_trade_index(t6)
    assert idx[0] == 4
    idx = hist.get_pair_trade_index(t7)
    assert idx[0] == 4
    assert idx[1] == 5
    idx = hist.get_pair_trade_index(t8)
    assert idx[0] == 4
    assert idx[1] == 5
    assert idx[2] == 3

def test_close():
    all_trades = [
        Trade(x=JPY('20000'), y=BTC('0.005'), order_id='JOR000001', t=pd.Timestamp(2022, 4, 1)),
        Trade(x=JPY('21000'), y=BTC('0.007'), order_id='JOR000002', t=pd.Timestamp(2022, 4, 1)),
        Trade(x=BTC('0.003'), y=JPY('12000'), order_id='JOR000003', t=pd.Timestamp(2022, 4, 1)),
        Trade(x=BTC('0.005'), y=JPY('25000'), order_id='JOR000004', t=pd.Timestamp(2022, 4, 1)),
        Trade(x=BTC('0.007'), y=JPY('28000'), order_id='JOR000005', t=pd.Timestamp(2022, 4, 1)),
        Trade(x=BTC('0.008'), y=JPY('32000'), order_id='JOR000006', t=pd.Timestamp(2022, 4, 1)),
        Trade(x=JPY('25000'), y=BTC('0.005'), order_id='JOR000007', t=pd.Timestamp(2022, 4, 1)),
        Trade(x=JPY('24000'), y=BTC('0.006'), order_id='JOR000008', t=pd.Timestamp(2022, 4, 1)),
        Trade(x=BTC('0.007'), y=JPY('21000'), order_id='JOR000009', t=pd.Timestamp(2022, 4, 1)),
        Trade(x=BTC('0.006'), y=JPY('24000'), order_id='JOR000010', t=pd.Timestamp(2022, 4, 1)),
    ]
    
    hist = History(all_trades)
    
    new_hist, report = hist.close()
    
    assert len(new_hist.df) == 2
    assert len(report.df) == 8
    
    hsm = hist.summarize()
    assert len(hsm) == 2
    assert hsm.iloc[0,0] == 'BTC'
    
    hsm = hist.summarize(origin='JPY')
    assert len(hsm) == 2
    assert hsm.iloc[0,0] == 'JPY'
    
    hsm = new_hist.summarize()
    assert len(hsm) == 1
    
    desc = new_hist.describe('BTC', 'JPY')
    assert desc['position'] == Fraction('47/4000')
    
    desc = new_hist.describe('JPY', 'BTC')
    assert desc['position'] == Fraction('0')
    