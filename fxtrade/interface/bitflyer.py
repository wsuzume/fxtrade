from __future__ import annotations

import json
import time
import hmac
import hashlib
import requests
from datetime import datetime
from fractions import Fraction
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin
from pydantic import BaseModel, validator


def build_signature(
    api_secret: str, method: str, endpoint: str, timestamp: str, body: Optional[str]
) -> str:
    message = "".join([timestamp, method, endpoint, body or ""])
    return hmac.new(
        api_secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def build_headers(
    api_key: str,
    api_secret: str,
    method: str,
    endpoint: str,
    body: Optional[str] = None,
) -> dict[str, str]:
    timestamp = str(time.time())
    signature = build_signature(api_secret, method, endpoint, timestamp, body)

    return {
        "Content-Type": "application/json",
        "ACCESS-KEY": api_key,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-SIGN": signature,
    }


def query_string(params: dict[str, Any]) -> str:
    return "&".join(f"{k}={v}" for k, v in params.items())


def send_request(
    base_url: str,
    endpoint: str,
    method: str = "GET",
    body: Optional[str] = None,
    params: Optional[dict[str, Any]] = None,
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
):
    endpoint_with_query = f"{endpoint}?{query_string(params)}" if params else endpoint

    url = urljoin(base_url, endpoint)
    request_func = {"GET": requests.get, "POST": requests.post}[method]

    headers = (
        build_headers(api_key, api_secret, method, endpoint_with_query, body)
        if api_key
        else None
    )

    return request_func(url, headers=headers, data=body, params=params)


#### Public API


### GET /v1/markets
def get_markets():
    base_url = "https://api.bitflyer.com"
    endpoint = "/v1/markets"

    return send_request(base_url, endpoint, method="GET")


class Market(BaseModel):
    product_code: str
    market_type: str

    @staticmethod
    def get() -> list[Market]:
        response = get_markets()
        response.raise_for_status()

        return [Market(**market) for market in response.json()]


### GET /v1/ticker
def get_ticker(product_code="BTC_JPY"):
    base_url = "https://api.bitflyer.com"
    endpoint = "/v1/ticker"

    params = {
        "product_code": product_code,
    }

    return send_request(base_url, endpoint, method="GET", params=params)


class Ticker(BaseModel):
    product_code: str
    state: str
    timestamp: datetime
    tick_id: int
    best_bid: Fraction
    best_ask: Fraction
    best_bid_size: Fraction
    best_ask_size: Fraction
    total_bid_depth: Fraction
    total_ask_depth: Fraction
    market_bid_size: Fraction
    market_ask_size: Fraction
    ltp: Fraction
    volume: Fraction
    volume_by_product: Fraction

    @validator(
        "best_bid",
        "best_ask",
        "best_bid_size",
        "best_ask_size",
        "total_bid_depth",
        "total_ask_depth",
        "market_bid_size",
        "market_ask_size",
        "ltp",
        "volume",
        "volume_by_product",
        pre=True,
    )
    def convert_to_fraction(cls, v):
        return Fraction(str(v))

    @staticmethod
    def get(product_code: str = "btc_jpy") -> Ticker:
        response = get_ticker(product_code=product_code)
        response.raise_for_status()
        return Ticker(**response.json())


### GET /v1/board
def get_board(product_code="BTC_JPY"):
    base_url = "https://api.bitflyer.com"
    endpoint = "/v1/board"

    params = {
        "product_code": product_code,
    }

    return send_request(base_url, endpoint, method="GET", params=params)


class Bid(BaseModel):
    price: Fraction
    size: Fraction

    @validator("price", "size", pre=True)
    def convert_to_fraction(cls, v):
        return Fraction(str(v))


class Ask(BaseModel):
    price: Fraction
    size: Fraction

    @validator("price", "size", pre=True)
    def convert_to_fraction(cls, v):
        return Fraction(str(v))


class Board(BaseModel):
    mid_price: float
    bids: List[Bid]
    asks: List[Ask]

    @staticmethod
    def get(product_code="BTC_JPY") -> Board:
        response = get_board(product_code=product_code)
        response.raise_for_status()
        return Board(**response.json())


### GET /v1/getboardstate
def get_boardstate(product_code: str = "BTC_JPY"):
    base_url = "https://api.bitflyer.com"
    endpoint = "/v1/getboardstate"

    params = {
        "product_code": product_code,
    }

    return send_request(base_url, endpoint, method="GET", params=params)


class BoardState(BaseModel):
    health: str
    state: str
    data: Optional[Dict[str, Any]] = None

    @staticmethod
    def get(product_code: str = "BTC_JPY") -> BoardState:
        response = get_boardstate(product_code=product_code)
        response.raise_for_status()
        return BoardState(**response.json())


### GET /v1/executions
def get_executions(
    product_code: str = "BTC_JPY",
    count: int | str = None,
    before: int | str = None,
    after: int | str = None,
):
    # 実行してみると count は max 500。
    # 500 以上を指定すると 500 個帰ってくるので
    # 最大個数返してはくれそう。
    # 戻り値は新しい取引から古い取引に遡る順で取得される。
    # before を指定するとその id よりも前の最新の 500 個を返す。
    # after を指定するとその id よりも後の最新の 500 個を返すことに注意。
    # 指定した id の直後の 500 個ではない。
    # before, after の両方を指定すると、before に近いほうから after まで遡る形式で取得される。
    base_url = "https://api.bitflyer.com"
    endpoint = "/v1/executions"

    params = {
        "product_code": product_code,
    }

    if count is not None:
        params["count"] = str(count)
    if before is not None:
        params["before"] = str(before)
    if after is not None:
        params["after"] = str(after)

    ### response.status_code
    # Success: 200
    # Failed: 400
    ### response.json()
    ## Success
    # [{
    #    'id': 2573873088,
    #    'side': 'BUY',
    #    'price': 16386697.0,
    #    'size': 0.01,
    #    'exec_date': '2025-01-26T07:33:31.74',
    #    'buy_child_order_acceptance_id': 'JRF20250126-073331-215275',
    #    'sell_child_order_acceptance_id': 'JRF20250126-073330-052100',
    # }, ...]
    ## Failed
    # {'status': -156, 'error_message': 'Execution history is limited to the most recent 31 days.', 'data': None}

    # before < after のときは、条件を満たす取引がないので Success: 200 で空リスト [] が返る。

    return send_request(base_url, endpoint, params=params)


def get_executions_backward(
    product_code: str = "BTC_JPY",
    count: int | str = 100,
    before: int | str = None,
    after: int | str = None,
    max_iter: int = 100,
    sleep: int | float = 1,
):
    ret = []
    for _ in range(max_iter):
        response = get_executions(
            product_code=product_code, count=count, before=before, after=after
        )

        if response.status_code != requests.codes.ok:
            # 通信エラーや取得できる範囲を超えて取得した場合
            ret.append(response)
            break

        exec_list = response.json()

        if len(exec_list) == 0:
            # before < after の関係になったなど、
            # 条件に一致する取引が存在しなくなった
            break

        # APIの挙動としては、before から after まで遡る方向に取得される。
        # よって取得したうちの最小の id が、次の最大の id となる。
        before = min([x["id"] for x in exec_list])

        # response をそのまま格納していき、
        # どのように扱うかは外部に任せる。
        ret.append(response)

        # rate limit は 0.6 秒くらいなので
        # 安全マージンを入れて 1 秒
        time.sleep(sleep)

    return ret


def extract_executions_from_responses(responses: list[requests.Response]):
    if len(responses) == 0:
        # max_iter が 0 のケース
        # エラーにしてもよいが、挙動としては正常といえる。
        return []

    if responses[0].status_code != requests.codes.ok:
        # １回目のリクエストが失敗しているなら指定の仕方が悪い可能性が高いのでエラー
        responses[0].raise_for_status()
    if responses[-1].status_code == requests.codes.bad_request:
        # １回目のリクエストが成功していて、それよりも後の末尾が 400 bad_request の場合、
        # 取得中に取得限界（30日前まで）に達した可能性が高い。
        # この場合は末尾のみ取り除けば残りは正常。
        responses.pop(-1)
    elif responses[-1].status_code != requests.codes.ok:
        # 200 ok か 400 bad_request 以外で終端している場合は、
        # 予期せぬエラーである可能性が高い。
        responses[-1].raise_for_status()

    exec_list = []
    for response in responses:
        exec_list.extend(response.json())

    return exec_list


class Execution(BaseModel):
    id: int
    side: str
    price: Fraction
    size: Fraction
    exec_date: datetime
    buy_child_order_acceptance_id: str
    sell_child_order_acceptance_id: str

    @validator("price", "size", pre=True)
    def convert_to_fraction(cls, v):
        return Fraction(str(v))

    @staticmethod
    def get(
        product_code: str = "BTC_JPY",
        count: int | str = None,
        before: int | str = None,
        after: int | str = None,
    ):
        response = get_executions(
            product_code=product_code, count=count, before=before, after=after
        )
        response.raise_for_status()
        return [Execution(**execution) for execution in response.json()]

    @staticmethod
    def get_backward(
        product_code: str = "BTC_JPY",
        count: int | str = None,
        before: int | str = None,
        after: int | str = None,
        max_iter: int = 500,
        sleep: int | float = 1,
    ):
        responses = get_executions_backward(
            product_code=product_code,
            count=count,
            before=before,
            after=after,
            max_iter=max_iter,
            sleep=sleep,
        )

        exec_list = extract_executions_from_responses(responses)

        return [
            Execution(**execution)
            for execution in sorted(exec_list, key=lambda x: x["id"])
        ]


### GET /v1/getfundingrate
def get_fundingrate(product_code: str):
    # market_type が 'FX' のもののみ指定可能。引数省略不可能。
    # 現在は FX_BTC_JPY のみ。

    base_url = "https://api.bitflyer.com"
    endpoint = "/v1/getboardstate"

    params = {
        "product_code": product_code,
    }

    return send_request(base_url, endpoint, method="GET", params=params)


class FundingRate(BaseModel):
    current_funding_rate: Fraction
    next_funding_rate_settledate: datetime

    @validator("current_funding_rate", pre=True)
    def convert_to_fraction(cls, v):
        return Fraction(str(v))

    @staticmethod
    def get(product_code: str) -> FundingRate:
        response = get_fundingrate(product_code=product_code)
        response.raise_for_status()
        return FundingRate(**response.json())


### GET /v1/getcorporateleverage
def get_corporateleverage():
    base_url = "https://api.bitflyer.com"
    endpoint = "/v1/getcorporateleverage"

    return send_request(base_url, endpoint, method="GET")


class CorporateLeverage(BaseModel):
    current_max: float
    current_startdate: datetime
    next_max: float
    next_startdate: datetime

    @validator("current_max", "next_max", pre=True)
    def convert_to_fraction(cls, v):
        return Fraction(str(v))

    @staticmethod
    def get() -> CorporateLeverage:
        response = get_corporateleverage()
        response.raise_for_status()
        return CorporateLeverage(**response.json())


### GET /v1/getchats
def get_chats(from_date: Optional[datetime] = None):
    # TODO: from_date を指定可能にする
    base_url = "https://api.bitflyer.com"
    endpoint = "/v1/getchats"

    # params = {
    #     "from_date": from_date,
    # }

    # return send_request(base_url, endpoint, method='GET', params=params)
    return send_request(base_url, endpoint, method="GET")


class Chat(BaseModel):
    nickname: str
    message: str
    date: datetime

    @staticmethod
    def get(from_date: Optional[datetime] = None):
        response = get_chats(from_date=from_date)
        response.raise_for_status()
        return [Chat(**chat) for chat in response.json()]


#### Private API


### GET /v1/me/getpermissions
def get_permissions(api_key: str, api_secret: str):
    base_url = "https://api.bitflyer.com"
    endpoint = "/v1/me/getpermissions"

    return send_request(
        base_url, endpoint, method="GET", api_key=api_key, api_secret=api_secret
    )


class Permissions(BaseModel):
    items: list[str]

    @staticmethod
    def get(api_key: str, api_secret: str):
        response = get_permissions(api_key=api_key, api_secret=api_secret)
        response.raise_for_status()
        return Permissions(items=response.json())


### GET /v1/me/gettradingcommission
def get_tradingcommission(api_key: str, api_secret: str, product_code: str):
    base_url = "https://api.bitflyer.com"
    endpoint = "/v1/me/gettradingcommission"

    params = {
        "product_code": product_code,
    }

    return send_request(
        base_url,
        endpoint,
        method="GET",
        params=params,
        api_key=api_key,
        api_secret=api_secret,
    )


class TradingCommission(BaseModel):
    commission_rate: Fraction

    @validator("commission_rate", pre=True)
    def convert_to_fraction(cls, v):
        return Fraction(str(v))

    @staticmethod
    def get(api_key: str, api_secret: str, product_code: str):
        response = get_tradingcommission(
            api_key=api_key, api_secret=api_secret, product_code=product_code
        )
        response.raise_for_status()
        return TradingCommission(**response.json())


### GET /v1/me/getbalance
def get_balance(api_key: str, api_secret: str):
    base_url = "https://api.bitflyer.com"
    endpoint = "/v1/me/getbalance"

    return send_request(
        base_url, endpoint, method="GET", api_key=api_key, api_secret=api_secret
    )


class Balance(BaseModel):
    currency_code: str
    amount: Fraction
    available: Fraction

    @validator("amount", "available", pre=True)
    def convert_to_fraction(cls, v):
        return Fraction(str(v))

    @staticmethod
    def get(api_key: str, api_secret: str) -> list[Balance]:
        response = get_balance(api_key=api_key, api_secret=api_secret)
        response.raise_for_status()
        return [Balance(**b) for b in response.json()]


### GET /v1/me/getbalancehistory
def get_balancehistory(
    api_key: str,
    api_secret: str,
    currency_code: str = "JPY",
    count: int = None,
    before: int = None,
    after: int = None,
):
    base_url = "https://api.bitflyer.com"
    endpoint = "/v1/me/getbalancehistory"

    params = {
        "currency_code": currency_code,
    }

    if count is not None:
        params["count"] = str(count)
    if before is not None:
        params["before"] = str(before)
    if after is not None:
        params["after"] = str(after)

    return send_request(
        base_url,
        endpoint,
        method="GET",
        params=params,
        api_key=api_key,
        api_secret=api_secret,
    )


class BalanceHistory(BaseModel):
    id: int
    trade_date: datetime
    event_date: datetime
    product_code: str
    currency_code: str
    trade_type: str
    price: Fraction
    amount: Fraction
    quantity: Fraction
    commission: Fraction
    balance: Fraction
    order_id: str

    @validator("price", "amount", "quantity", "commission", "balance", pre=True)
    def convert_to_fraction(cls, v):
        return Fraction(str(v))

    @staticmethod
    def get(
        api_key: str,
        api_secret: str,
        currency_code: str = "JPY",
        count: int = None,
        before: int = None,
        after: int = None,
    ):
        response = get_balancehistory(
            api_key=api_key,
            api_secret=api_secret,
            currency_code=currency_code,
            count=count,
            before=before,
            after=after,
        )
        response.raise_for_status()
        return [BalanceHistory(**bh) for bh in response.json()]


# # def get_child_orders(api_key, api_secret, product_code='btc_jpy'):
# #     base_url = 'https://api.bitflyer.com'
# #     endpoint = '/v1/me/getchildorders'

# #     params = {
# #         "product_code": product_code,
# #         "count": str(100),
# #     }

# #     return send_request(base_url, endpoint, method='GET', params=params, api_key=api_key, api_secret=api_secret)


### POST /v1/me/cancelchildorder
def send_cancelchildorder(
    *,
    api_key: str,
    api_secret: str,
    product_code: str,
    child_order_id: str = None,
    child_order_acceptance_id: str = None,
):
    base_url = "https://api.bitflyer.com"
    endpoint = "/v1/me/cancelchildorder"

    if (child_order_id is None) and (child_order_acceptance_id is None):
        raise TypeError(
            "child_order_id xor child_order_acceptance_id must be specified."
        )
    elif (child_order_id is not None) and (child_order_acceptance_id is not None):
        raise TypeError(
            "child_order_id xor child_order_acceptance_id must be specified."
        )
    elif child_order_id is not None:
        body = {
            "product_code": product_code,
            "child_order_id": child_order_id,
        }
    elif child_order_acceptance_id is not None:
        body = {
            "product_code": product_code,
            "child_order_acceptance_id": child_order_acceptance_id,
        }
    else:
        raise RuntimeError("unknown error.")

    body = json.dumps(body)

    return send_request(
        base_url,
        endpoint,
        method="POST",
        body=body,
        api_key=api_key,
        api_secret=api_secret,
    )


class ChildOrderResponse(BaseModel):
    # product_code は本来レスポンスに含まれないが、キャンセル時には必須パラメータなのでセットにしておく。
    product_code: str
    child_order_acceptance_id: str

    def send(self, api_key: str, api_secret: str):
        response = send_cancelchildorder(
            api_key=api_key, api_secret=api_secret, **self.model_dump()
        )
        response.raise_for_status()
        return response


### POST /v1/me/sendchildorder
def send_childorder(
    *,
    api_key: str,
    api_secret: str,
    product_code: str,
    child_order_type: str,
    side: str,
    price: Optional[int] = None,
    size: float,
    minute_to_expire: int = 43200,
    time_in_force: str = "GTC",
):
    base_url = "https://api.bitflyer.com"
    endpoint = "/v1/me/sendchildorder"

    if child_order_type not in {"LIMIT", "MARKET"}:
        raise ValueError("")
    if side not in {"BUY", "SELL"}:
        raise ValueError("")

    body = {}
    body["product_code"] = product_code
    body["child_order_type"] = child_order_type  # 指値なら 'LIMIT', 成行なら 'MARKET'
    body["side"] = side  # 買いなら 'BUY', 売りなら 'SELL'
    if (child_order_type == "LIMIT") and (price is None):
        raise ValueError("price must be specified when child_order_type == 'LIMIT'")
    elif (child_order_type == "MARKET") and (price is None):
        # 成行注文でも price の指定は可能なようだが、どのような挙動になるかは不明。
        pass
    else:
        body["price"] = price  # 価格の指定
    body["size"] = size  # 注文数量
    body["minute_to_expire"] = minute_to_expire  # 期限切れまでの時間（分）
    body["time_in_force"] = time_in_force  # 執行数量条件

    body = json.dumps(body)

    return send_request(
        base_url,
        endpoint,
        method="POST",
        body=body,
        api_key=api_key,
        api_secret=api_secret,
    )


class ChildOrder(BaseModel):
    product_code: str
    child_order_type: str  # 'LIMIT' or 'MARKET'
    side: str  # 'BUY' or 'SELL'
    price: Optional[int]  # necessary if child_order_type == 'MARKET'
    size: float
    minute_to_expire: int  # default 43200 (30days)
    time_in_force: str  # 'GTC', 'IOC', or 'FOK' (default 'GTC')

    @staticmethod
    def buy(
        product_code: str,
        child_order_type: str,
        price: int,
        size: float,
        minute_to_expire: int = 43200,
        time_in_force: str = "GTC",
    ):
        return ChildOrder(
            product_code=product_code,
            child_order_type=child_order_type,
            side="BUY",
            price=price,
            size=size,
            minute_to_expire=minute_to_expire,
            time_in_force=time_in_force,
        )

    @staticmethod
    def sell(
        product_code: str,
        child_order_type: str,
        price: int,
        size: float,
        minute_to_expire: int = 43200,
        time_in_force: str = "GTC",
    ):
        return ChildOrder(
            product_code=product_code,
            child_order_type=child_order_type,
            side="SELL",
            price=price,
            size=size,
            minute_to_expire=minute_to_expire,
            time_in_force=time_in_force,
        )

    @staticmethod
    def limit_buy(
        product_code: str,
        price: int,
        size: float,
        minute_to_expire: int = 43200,
        time_in_force: str = "GTC",
    ):
        """指値注文"""
        return ChildOrder(
            product_code=product_code,
            child_order_type="LIMIT",
            side="BUY",
            price=price,
            size=size,
            minute_to_expire=minute_to_expire,
            time_in_force=time_in_force,
        )

    @staticmethod
    def market_buy(
        product_code: str,
        size: float,
        minute_to_expire: int = 43200,
        time_in_force: str = "GTC",
    ):
        """成行注文"""
        return ChildOrder(
            product_code=product_code,
            child_order_type="MARKET",
            side="BUY",
            price=None,
            size=size,
            minute_to_expire=minute_to_expire,
            time_in_force=time_in_force,
        )

    @staticmethod
    def limit_sell(
        product_code: str,
        price: int,
        size: float,
        minute_to_expire: int = 43200,
        time_in_force: str = "GTC",
    ):
        """指値注文"""
        return ChildOrder(
            product_code=product_code,
            child_order_type="LIMIT",
            side="SELL",
            price=price,
            size=size,
            minute_to_expire=minute_to_expire,
            time_in_force=time_in_force,
        )

    @staticmethod
    def market_sell(
        product_code: str,
        size: float,
        minute_to_expire: int = 43200,
        time_in_force: str = "GTC",
    ):
        """成行注文"""
        return ChildOrder(
            product_code=product_code,
            child_order_type="MARKET",
            side="SELL",
            price=None,
            size=size,
            minute_to_expire=minute_to_expire,
            time_in_force=time_in_force,
        )

    def send(self, api_key: str, api_secret: str):
        response = send_childorder(
            api_key=api_key, api_secret=api_secret, **self.model_dump()
        )
        response.raise_for_status()
        return ChildOrderResponse(product_code=self.product_code, **response.json())
