import pytest

from fxtrade.interface.yfinance import response_to_dataframe, YahooFinanceAPI
from requests import HTTPError

def test_response_to_dataframe():
    import pickle
    with open('tests/data/response.pickle', 'rb') as f:
        resp = pickle.load(f)
    
    df = response_to_dataframe(resp)

    assert df.shape == (5, 6)

def test_YahooFinanceAPI():
    assert 'BTC-JPY' == YahooFinanceAPI.make_ticker('BTC', 'JPY')

    api = YahooFinanceAPI(api_key='***')

    assert 'BTC-JPY' in api.tickers
    assert 'USD-JPY' in api.tickers

    assert '10y' in api.cranges
    assert '1mo' in api.cranges
    assert '5d' in api.cranges

    assert '1d' in api.intervals
    assert '15m' in api.intervals
    assert '1m' in api.intervals

    assert '10y' == api.max_cranges['1d']
    assert '1mo' == api.max_cranges['15m']
    assert '5d' == api.max_cranges['1m']

    assert '10y-1d' in api.default_timestamp_filter
    assert '1mo-15m' in api.default_timestamp_filter
    assert '5d-1m' in api.default_timestamp_filter

    assert '10y-1d' in api.default_save_fstring
    assert '1mo-15m' in api.default_save_fstring
    assert '5d-1m' in api.default_save_fstring

    assert '10y-1d' in api.default_save_iterator
    assert '1mo-15m' in api.default_save_iterator
    assert '5d-1m' in api.default_save_iterator

    with pytest.raises(HTTPError):
        # this code will be resulted in 403 client error because
        # we didn't specify the api_key
        api.download('BTC-JPY', '10y', '1d')