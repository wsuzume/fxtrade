import unittest

import pandas as pd

from fractions import Fraction

from fxtrade.stock import Stock, Rate
from fxtrade.stocks import JPY, BTC
from fxtrade.trade import Trade, History


class TestTrade(unittest.TestCase):
    def test_init(self):
        x = JPY(20000)
        y = BTC('0.005')
        
        t = Trade(x, y)
        
        self.assertEqual(t.rate, Rate.from_stocks(x, y))
    
    def test_split(self):
        x1 = JPY(20000)
        y1 = BTC('0.005')
        
        x2 = JPY(5000)
        y2 = BTC('0.003')
        
        t = Trade(x1, y1)
        
        z1, z2 = t.split(x2)
        z3, z4 = t.split(y2)
        
        self.assertEqual(z1.x, x2)
        self.assertEqual(z2.x, JPY(15000))
        self.assertEqual(z1.y, BTC('0.00125'))
        self.assertEqual(z2.y, BTC('0.00375'))
        
        self.assertEqual(z3.x, JPY(12000))
        self.assertEqual(z4.x, JPY(8000))
        self.assertEqual(z3.y, y2)
        self.assertEqual(z4.y, BTC('0.002'))
        
        x3 = JPY(30000)
        y3 = BTC('0.006')
        a3 = Stock('USD', 2000)
        
        with self.assertRaises(ValueError):
            t.split(x3)
        with self.assertRaises(ValueError):
            t.split(y3)
        with self.assertRaises(TypeError):
            t.split(a3)
        
        with self.assertRaises(ValueError):
            t.split_x(x3)
        with self.assertRaises(ValueError):
            t.split_y(y3)
        with self.assertRaises(TypeError):
            t.split_x(a3)
        with self.assertRaises(TypeError):
            t.split_y(a3)
    
    def test_settle(self):
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
        self.assertIsNone(unsettled)
        
        tp, unsettled = t1.settle(t3)
        self.assertEqual(unsettled.y, BTC('0.001'))
        
        tp, unsettled = t1.settle(t4)
        self.assertEqual(unsettled.x, BTC('0.001'))
        
        with self.assertRaises(ValueError):
            t1.settle(t5)

class TestHistory(unittest.TestCase):
    def test_init(self):
        hist = History()
        
        self.assertEqual(len(hist.df), 0)
    
    def test_functions(self):
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
        
        self.assertEqual(len(hist.df), 1)
        
        hist.add(all_trades)
        
        self.assertEqual(len(hist.df), 11)
        
        hist.drop([0, 1, 2])
        
        self.assertEqual(len(hist.df), 8)
        
        ts = hist.as_trade_list()
        
        self.assertEqual(len(ts), 8)
    
    def test_get_pair_trade_index(self):
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
        self.assertEqual(idx[0], 1)
        idx = hist.get_pair_trade_index(t2)
        self.assertEqual(idx[0], 1)
        idx = hist.get_pair_trade_index(t3)
        self.assertEqual(idx[0], 1)
        self.assertEqual(idx[1], 2)
        idx = hist.get_pair_trade_index(t4)
        self.assertEqual(idx[0], 1)
        self.assertEqual(idx[1], 2)
        self.assertEqual(idx[2], 0)
        
        idx = hist.get_pair_trade_index(t5)
        self.assertEqual(idx[0], 4)
        idx = hist.get_pair_trade_index(t6)
        self.assertEqual(idx[0], 4)
        idx = hist.get_pair_trade_index(t7)
        self.assertEqual(idx[0], 4)
        self.assertEqual(idx[1], 5)
        idx = hist.get_pair_trade_index(t8)
        self.assertEqual(idx[0], 4)
        self.assertEqual(idx[1], 5)
        self.assertEqual(idx[2], 3)
    
    def test_close(self):
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
        
        self.assertEqual(len(new_hist.df), 2)
        self.assertEqual(len(report.df), 8)
        
        hsm = hist.summarize()
        self.assertEqual(len(hsm), 2)
        self.assertEqual(hsm.iloc[0,0], 'BTC')
        
        hsm = hist.summarize(origin='JPY')
        self.assertEqual(len(hsm), 2)
        self.assertEqual(hsm.iloc[0,0], 'JPY')
        
        hsm = new_hist.summarize()
        self.assertEqual(len(hsm), 1)
        
        desc = new_hist.describe('BTC', 'JPY')
        self.assertEqual(desc['position'], Fraction('47/4000'))
        
        desc = new_hist.describe('JPY', 'BTC')
        self.assertEqual(desc['position'], Fraction('0'))
        
    
if __name__ == "__main__":
    unittest.main()