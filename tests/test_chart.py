import pytest
import pandas as pd

from fxtrade.api import CodePair, CrangePeriod
from fxtrade.chart import ChartDummyAPI, Board, Chart

def test_ChartDummyAPI():
    api = ChartDummyAPI()

    assert api.default_crange_period == CrangePeriod('max', '15m')
    assert api.is_valid_crange_period(CrangePeriod('max', '15m'))
    assert not api.is_valid_crange_period(CrangePeriod('max', 'xxx'))
    assert isinstance(api.empty, pd.DataFrame)

def test_Board_dummy():
    board = Board(api=ChartDummyAPI(),
                code_pair=CodePair('BTC', 'JPY'),
                crange_period=CrangePeriod('max', '15m'),
            )
    
    assert board.dumps() == \
        "Board(api=ChartDummyAPI(),\n" + \
        "    code_pair='CodePair(base='BTC', quote='JPY')',\n" + \
        "    crange_period='CrangePeriod(crange='max', period='15m')',\n" + \
        "    interval=None,\n" + \
        "    first_updated=None,\n" + \
        "    last_updated=None,\n" + \
        ")"

def test_Chart_make_crange_period_list():
    chart = Chart(api=ChartDummyAPI(),
                code_pair=CodePair('BTC', 'JPY'),
                data_dir='../data/chart',
                crange_period=[],
            )
    

    xs = chart._make_crange_period_list('max-15m')
    assert CrangePeriod('max', '15m') in xs

    xs = chart._make_crange_period_list(CrangePeriod('max', '15m'))
    assert CrangePeriod('max', '15m') in xs

    xs = chart._make_crange_period_list(['max-15m', CrangePeriod('max', '1m')])
    assert CrangePeriod('max', '15m') in xs
    assert CrangePeriod('max', '1m') in xs

    with pytest.raises(TypeError):
        chart._make_crange_period_list(3.14)
    
    with pytest.raises(TypeError):
        chart._make_crange_period_list([3.14])

def test_Chart_make_crange_period_dict():
    chart = Chart(api=ChartDummyAPI(),
                code_pair=CodePair('BTC', 'JPY'),
                data_dir='../data/chart',
                crange_period=[],
            )
    
    assert 'max-15m' in chart._make_crange_period_dict('max-15m')
    assert CrangePeriod('max', '15m') in chart._make_crange_period_dict(CrangePeriod('max', '15m'))

    xs = chart._make_crange_period_dict(['max-1m', CrangePeriod('max', '15m')])
    assert 'max-1m' in xs
    assert CrangePeriod('max', '15m') in xs

    xs = chart._make_crange_period_dict({
        'dairy': 'max-1d',
        'max-15m': CrangePeriod('max', '15m')
    })

    assert 'dairy' in xs
    assert 'max-15m' in xs

    with pytest.raises(TypeError):
        chart._make_crange_period_dict({
            'dairy': 3.14,
        })
    
    with pytest.raises(TypeError):
        chart._make_crange_period_dict({
            3.14: 'max-15m',
        })
    
    xs = chart._make_crange_period_dict({
        'max-15m': ...,
        CrangePeriod('max', '1m'): ...,
    })

    assert 'max-15m' in xs
    assert CrangePeriod('max', '1m') in xs

    with pytest.raises(ValueError):
        chart._make_crange_period_dict({
            CrangePeriod('max', '1m'): CrangePeriod('max', '1h'),
        })

def test_Chart_dummy():
    chart = Chart(api=ChartDummyAPI(),
                code_pair=CodePair('BTC', 'JPY'),
                data_dir='../data/chart',
                crange_period=[CrangePeriod('max', '15m')],
            )
    
    assert chart.dumps() == \
        "Chart(api=ChartDummyAPI(),\n" + \
        "    code_pair=CodePair(base='BTC', quote='JPY'),\n" + \
        "    data_dir='../data/chart',\n" + \
        "    crange_period=[CrangePeriod(crange='max', period='15m')],\n" + \
        "    board={\n" + \
        "        'CrangePeriod(crange='max', period='15m')': Board(api=ChartDummyAPI(),\n" + \
        "            code_pair='CodePair(base='BTC', quote='JPY')',\n" + \
        "            crange_period='CrangePeriod(crange='max', period='15m')',\n" + \
        "            interval=None,\n" + \
        "            first_updated=None,\n" + \
        "            last_updated=None,\n" + \
        "        ),\n" + \
        "    }\n" + \
        ")"
    
    chart.add(crange_period=CrangePeriod('max', '1d'), name='dairy')


# def test_TickerCrangeIntervals():
#     tci = TickerCrangeIntervals()

#     tci.add('USD-JPY')

#     assert 'USD-JPY' in tci

#     tci.add('BTC-JPY', '1mo-15m')

#     assert '1mo-15m' in tci['BTC-JPY']

#     tci.add('BTC-JPY', {
#         'aa': 'bb',
#         'cc': 'dd',
#     })

#     assert 'aa' in tci['BTC-JPY']
#     assert tci['BTC-JPY']['aa'] == 'bb'

#     tci.add('BTC-JPY', ['ee', 'ff'])

#     assert 'ee' in tci['BTC-JPY']
#     assert tci['BTC-JPY']['ee'] == 'ee'

#     # this code resets and overwrites tci['BTC-JPY']
#     tci['BTC-JPY'] = {
#         'aa': 'bb',
#         'cc': 'dd',
#     }

#     assert 'aa' in tci['BTC-JPY']
#     assert tci['BTC-JPY']['aa'] == 'bb'
#     assert 'ee' not in tci['BTC-JPY']

#     with pytest.raises(TypeError):
#         tci.add(4)

# from glob import glob

# def test_SingleChart():
#     print(glob('tests/emulator/*'))
#     #assert False