import pytest

from fxtrade.api import CodePair
from fxtrade.stocks import BTC
from fxtrade.chart import ChartDummyAPI, Chart
from fxtrade.trader import TraderDummyAPI, Trader

def test_TraderDummyAPI():
    api = TraderDummyAPI()

    assert api.minimum_order_quantity('BTC') == BTC('0.001')
    assert api.maximum_order_quantity('BTC') == BTC('1000')

def test_Trader():
    chart = Chart(api=ChartDummyAPI(),
              code_pair=CodePair('BTC', 'JPY'),
              data_dir='../data/chart',
              crange_period=[],
            )
    
    trader = Trader(
        api=TraderDummyAPI(),
        code_pair=CodePair('BTC', 'JPY'),
        chart=chart,
        history=None,
        data_dir='../data/trader',
    )
