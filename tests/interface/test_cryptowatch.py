import pytest

from fxtrade.api import CodePair, CrangePeriod
from fxtrade.interface.cryptowatch import CryptowatchAPI

def test_CryptowatchAPI():
    api = CryptowatchAPI(api_key='xxxx')

    assert api.make_code_pair_string('BTC', 'JPY') == 'btcjpy'
    assert api.make_code_pair_string(CodePair('BTC', 'JPY')) == 'btcjpy'
    assert api.default_crange_period == CrangePeriod('max', '15m')
