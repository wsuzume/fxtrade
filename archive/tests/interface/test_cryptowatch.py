import pytest
import pickle

import pandas as pd

from requests.exceptions import HTTPError

from fxtrade.api import CodePair, CRangePeriod
from fxtrade.interface.cryptowatch import response_to_dataframe, CryptowatchAPI

def test_response_to_dataframe():
    path = './tests/data/cryptowatch_response.pkl'
    with open(path, 'rb') as f:
        resp = pickle.load(f)
    
    df = response_to_dataframe(resp)

    assert isinstance(df, pd.DataFrame)

def test_CryptowatchAPI():
    api = CryptowatchAPI(api_key='xxxx')

    assert api.make_code_pair_string('BTC', 'JPY') == 'btcjpy'
    assert api.make_code_pair_string(CodePair('BTC', 'JPY')) == 'btcjpy'
    assert api.default_crange_period == CRangePeriod('max', '15m')

    with pytest.raises(HTTPError):
        api.download(CodePair('BTC', 'JPY'))
