import pytest

from fxtrade.chart import ChartDummyAPI
from fxtrade.trader import TraderDummyAPI, Trader
from fxtrade.fx import FX

def test_FX():
    chart_api = ChartDummyAPI()
    trader_api = TraderDummyAPI()

    fx = FX(name='trader1',
            origin='JPY',
            chart_api=chart_api,
            trader_api=trader_api,
            data_dir='../data')
    
    fx.generate_client('BTC', crange_period=[])

    assert fx.dumps() == \
        "FX(name='trader1',\n" + \
        "    origin='JPY',\n" + \
        "    data_dir='../data/trader1',\n" + \
        "    markets={\n" + \
        "        'BTC': Trader(api=TraderDummyAPI(),\n" + \
        "            code_pair=CodePair(base='BTC', quote='JPY'),\n" + \
        "            data_dir='../data/trader1/trader',\n" + \
        "            wallet=Wallet({\n" + \
        "                'BTC': Stock(BTC, 0),\n" + \
        "                'JPY': Stock(JPY, 0),\n" + \
        "            }),\n" + \
        "            chart=Chart(api=ChartDummyAPI(),\n" + \
        "                code_pair=CodePair(base='BTC', quote='JPY'),\n" + \
        "                data_dir='../data/trader1/chart',\n" + \
        "                crange_period=[],\n" + \
        "                board={\n" + \
        "                }\n" + \
        "            )\n" + \
        "        ),\n" + \
        "    }\n" + \
        ")"

    assert isinstance(fx['BTC'], Trader)

# def test_FX_exceptions():
#     fx = FX(name='FX', origin='JPY')

#     assert fx.dumps() == \
#         "FX(origin='JPY',\n" + \
#         "    data_dir='None',\n" + \
#         "    markets={\n" + \
#         "    }\n" + \
#         ")"