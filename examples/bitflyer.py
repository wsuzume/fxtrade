import os
import sys
from pathlib import Path

cwd = Path.cwd()
if str(cwd) not in sys.path:
    sys.path.append(str(cwd))


def get_apikeys():
    home_path = Path(os.environ["HOME"])
    config_path = home_path / ".config/fxtrade/bitflyer.json"

    with open(config_path, "r") as f:
        data = json.load(f)
        api_key = data["api_key"]
        api_secret = data["api_secret"]

    return api_key, api_secret


###

import json
from pprint import pprint

# Public API
from fxtrade.interface.bitflyer import (
    Board,
    BoardState,
    Chat,
    CorporateLeverage,
    Execution,
    Market,
    Ticker,
)


def public_api_example():
    ### Public API

    markets = Market.get()
    # pprint(markets)

    board = Board.get(product_code="BTC_JPY")
    # pprint(board)

    board_state = BoardState.get(product_code="BTC_JPY")
    # pprint(board_state)

    ticker = Ticker.get(product_code="BTC_JPY")
    # pprint(ticker)

    executions = Execution.get(product_code="BTC_JPY", count=10)
    # pprint(executions)

    cl = CorporateLeverage.get()
    # pprint(cl)

    chats = Chat.get()
    # pprint(chats)


# Private API
from fxtrade.interface.bitflyer import (
    Balance,
    BalanceHistory,
    Permissions,
    TradingCommission,
)


def private_api_example():
    # APIキーの取得
    api_key, api_secret = get_apikeys()

    # APIキーに許可されている操作
    permissions = Permissions.get(api_key=api_key, api_secret=api_secret)
    # pprint(permissions)

    # 取引手数料
    commission = TradingCommission.get(
        api_key=api_key, api_secret=api_secret, product_code="BTC_JPY"
    )
    # pprint(commission)

    # 残高
    balances = Balance.get(api_key=api_key, api_secret=api_secret)
    # pprint(balances)

    # 残高の推移
    balance_histories = BalanceHistory.get(
        api_key=api_key, api_secret=api_secret, currency_code="JPY", count=10
    )
    # pprint(balance_histories)


# 実際に注文する
from fxtrade.interface.bitflyer import ChildOrder
from fxtrade.math import floor


def limit_buy():
    # 使わないのでテストしていない

    # APIキーの取得
    api_key, api_secret = get_apikeys()

    order = ChildOrder.limit_buy(product_code="BTC_JPY", price=12594320, size=0.001)

    # 発注する
    acceptance = order.send(api_key=api_key, api_secret=api_secret)
    pprint(acceptance)

    # 注文をキャンセルする
    response = acceptance.cancel(api_key=api_key, api_secret=api_secret)
    pprint(response)


def market_buy():
    # APIキーの取得
    api_key, api_secret = get_apikeys()

    order = ChildOrder.market_buy(product_code="BTC_JPY", size=0.001)
    response = order.send(api_key=api_key, api_secret=api_secret)
    print(response)


def market_sell():
    # APIキーの取得
    api_key, api_secret = get_apikeys()

    # 取引手数料の取得
    commission = TradingCommission.get(
        api_key=api_key, api_secret=api_secret, product_code="BTC_JPY"
    )

    # Bitcoin残高の取得
    balances = {
        b.currency_code: b for b in Balance.get(api_key=api_key, api_secret=api_secret)
    }

    pprint(commission)
    pprint(balances["BTC"])

    # 取引手数料の割合
    r = commission.commission_rate
    # 取引可能残高
    M = balances["BTC"].available

    # 売却可能最大数量
    # bitflyer で指定可能な小数点以下6桁目までで切り捨てておく
    m = floor(M / (1 + r), 6)

    # 売却可能最大数量に手数料を足した額が、取引可能残高よりも小さくないといけない
    assert m + m * r <= M

    print("Max available:", M)
    print("Max salable", m)
    print("Max salable + commission", m + m * r)

    order = ChildOrder.market_sell(product_code="BTC_JPY", size=m)
    response = order.send(api_key=api_key, api_secret=api_secret)
    print(response)


if __name__ == "__main__":
    public_api_example()
    # private_api_example()

    ### 実際に取引が行われるので注意！！
    # market_buy()

    ### 実際に取引が行われるので注意！！
    # market_sell()
