import pytest

from requests.exceptions import HTTPError

from fxtrade.code import CodePair
from fxtrade.stock import Stock
from fxtrade.interface.bitflyer import BitflyerAPI

def test_BitflyerAPI():
    api = BitflyerAPI(api_key='xxxx', api_secret='xxxx')

    assert api.make_code_pair_string('BTC', 'JPY') == 'BTC_JPY'
    assert api.make_code_pair_string(CodePair('BTC', 'JPY')) == 'BTC_JPY'

    assert api.minimum_order_quantity(CodePair('BTC', 'JPY')) == Stock('BTC', '0.001')
    assert api.maximum_order_quantity(CodePair('BTC', 'JPY')) == Stock('BTC', '1000')

    # ネットワークに接続した状態で実施する
    with pytest.raises(HTTPError):
        api.download_wallet()