import pytest

from fxtrade.api import CodePair
from fxtrade.interface.bitflyer import BitflyerAPI

def test_BitflyerAPI():
    api = BitflyerAPI(api_key='xxxx', api_secret='xxxx')

    assert api.make_code_pair_string('BTC', 'JPY') == 'BTC_JPY'
    assert api.make_code_pair_string(CodePair('BTC', 'JPY')) == 'BTC_JPY'