from __future__ import annotations

import time
import hmac
import hashlib
import requests
from datetime import datetime
from fractions import Fraction
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin
from pydantic import BaseModel, validator

def build_signature(api_secret: str, method: str, endpoint: str, timestamp: str, body: Optional[str]) -> str:
    message = ''.join([timestamp, method, endpoint, body or ''])
    return hmac.new(
        api_secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def build_headers(api_key: str, api_secret: str, method: str, endpoint: str, body: Optional[str] = None) ->dict[str, str]:
    timestamp = str(time.time())
    signature = build_signature(api_secret, method, endpoint, timestamp, body)
    
    return {
        'Content-Type': 'application/json',
        'ACCESS-KEY': api_key,
        'ACCESS-TIMESTAMP': timestamp,
        'ACCESS-SIGN': signature
    }

def query_string(params: dict[str, Any]) -> str:
    return '&'.join(f'{k}={v}' for k, v in params.items())

def send_request(
    base_url: str,
    endpoint: str,
    method: str = 'GET',
    body: Optional[str] = None,
    params: Optional[dict[str, Any]] = None,
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None
):
    endpoint_with_query = f'{endpoint}?{query_string(params)}' if params else endpoint

    url = urljoin(base_url, endpoint)
    request_func = {'GET': requests.get, 'POST': requests.post}[method]

    headers = build_headers(api_key, api_secret, method, endpoint_with_query, body) if api_key else None

    return request_func(url, headers=headers, data=body, params=params)

#### Public API

### GET /v1/markets
def get_markets():
    base_url = 'https://api.bitflyer.com'
    endpoint = '/v1/markets'

    return send_request(base_url, endpoint, method='GET')

class Market(BaseModel):
    product_code: str
    market_type: str

    @staticmethod
    def get() -> list[Market]:
        response = get_markets()
        response.raise_for_status()

        return [ Market(**market) for market in response.json() ]

### GET /v1/ticker
def get_ticker(product_code='BTC_JPY'):
    base_url = 'https://api.bitflyer.com'
    endpoint = '/v1/ticker'
    
    params = {
        "product_code": product_code,
    }
    
    return send_request(base_url, endpoint, method='GET', params=params)

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
        'best_bid', 'best_ask',
        'best_bid_size', 'best_ask_size',
        'total_bid_depth', 'total_ask_depth',
        'market_bid_size', 'market_ask_size',
        'ltp', 'volume', 'volume_by_product',
        pre=True
    )
    def convert_to_fraction(cls, v):
        return Fraction(str(v))

    @staticmethod
    def get(product_code: str='btc_jpy') -> Ticker:
        response = get_ticker(product_code=product_code)
        response.raise_for_status()
        return Ticker(**response.json())

### GET /v1/board
def get_board(product_code='BTC_JPY'):
    base_url = 'https://api.bitflyer.com'
    endpoint = '/v1/board'
    
    params = {
        "product_code": product_code,
    }
    
    return send_request(base_url, endpoint, method='GET', params=params)

class Bid(BaseModel):
    price: Fraction
    size: Fraction

    @validator('price', 'size', pre=True)
    def convert_to_fraction(cls, v):
        return Fraction(str(v))

class Ask(BaseModel):
    price: Fraction
    size: Fraction

    @validator('price', 'size', pre=True)
    def convert_to_fraction(cls, v):
        return Fraction(str(v))

class Board(BaseModel):
    mid_price: float
    bids: List[Bid]
    asks: List[Ask]

    @staticmethod
    def get(product_code='BTC_JPY') -> Board:
        response = get_board(product_code=product_code)
        response.raise_for_status()
        return Board(**response.json())

### GET /v1/getboardstate
def get_boardstate(product_code: str='BTC_JPY'):
    base_url = 'https://api.bitflyer.com'
    endpoint = '/v1/getboardstate'
    
    params = {
        "product_code": product_code,
    }
    
    return send_request(base_url, endpoint, method='GET', params=params)

class BoardState(BaseModel):
    health: str
    state: str
    data: Optional[Dict[str, Any]] = None

    @staticmethod
    def get(product_code: str='BTC_JPY') -> BoardState:
        response = get_boardstate(product_code=product_code)
        response.raise_for_status()
        return BoardState(**response.json())

### GET /v1/executions
def get_executions(product_code: str='BTC_JPY', count: int | str=None, before: int | str=None, after: int | str=None):
    # 実行してみると count は max 500。
    # 500 以上を指定すると 500 個帰ってくるので
    # 最大個数返してはくれそう。
    # 戻り値は新しい取引から古い取引に遡る順で取得される。
    # before を指定するとその id よりも前の最新の 500 個を返す。
    # after を指定するとその id よりも後の最新の 500 個を返すことに注意。
    # 指定した id の直後の 500 個ではない。
    # before, after の両方を指定すると、before に近いほうから after まで遡る形式で取得される。
    base_url = 'https://api.bitflyer.com'
    endpoint = '/v1/executions'
    
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

class Execution(BaseModel):
    id: int
    side: str
    price: Fraction
    size: Fraction
    exec_date: datetime
    buy_child_order_acceptance_id: str
    sell_child_order_acceptance_id: str

    @validator('price', 'size', pre=True)
    def convert_to_fraction(cls, v):
        return Fraction(str(v))

    @staticmethod
    def get(product_code: str='BTC_JPY', count: int | str=None, before: int | str=None, after: int | str=None):
        response = get_executions(product_code=product_code, count=count, before=before, after=after)
        response.raise_for_status()
        return [ Execution(**execution) for execution in response.json() ]

### GET /v1/getfundingrate
def get_fundingrate(product_code: str):
    # market_type が 'FX' のもののみ指定可能。引数省略不可能。
    # 現在は FX_BTC_JPY のみ。
    
    base_url = 'https://api.bitflyer.com'
    endpoint = '/v1/getboardstate'
    
    params = {
        "product_code": product_code,
    }
    
    return send_request(base_url, endpoint, method='GET', params=params)

class FundingRate(BaseModel):
    current_funding_rate: Fraction
    next_funding_rate_settledate: datetime

    @validator('current_funding_rate', pre=True)
    def convert_to_fraction(cls, v):
        return Fraction(str(v))

    @staticmethod
    def get(product_code: str) -> FundingRate:
        response = get_fundingrate(product_code=product_code)
        response.raise_for_status()
        return FundingRate(**response.json())

### GET /v1/getcorporateleverage
def get_corporateleverage():
    base_url = 'https://api.bitflyer.com'
    endpoint = '/v1/getcorporateleverage'
    
    return send_request(base_url, endpoint, method='GET')

class CorporateLeverage(BaseModel):
    current_max: float
    current_startdate: datetime
    next_max: float
    next_startdate: datetime

    @validator('current_max', 'next_max', pre=True)
    def convert_to_fraction(cls, v):
        return Fraction(str(v))

    @staticmethod
    def get() -> CorporateLeverage:
        response = get_corporateleverage()
        response.raise_for_status()
        return CorporateLeverage(**response.json())

### GET /v1/getchats
def get_chats(from_date: Optional[datetime]=None):
    # TODO: from_date を指定可能にする
    base_url = 'https://api.bitflyer.com'
    endpoint = '/v1/getchats'
    
    # params = {
    #     "from_date": from_date,
    # }
    
    #return send_request(base_url, endpoint, method='GET', params=params)
    return send_request(base_url, endpoint, method='GET')

class Chat(BaseModel):
    nickname: str
    message: str
    date: datetime

    @staticmethod
    def get(from_date: Optional[datetime]=None):
        response = get_chats(from_date=from_date)
        response.raise_for_status()
        return [ Chat(**chat) for chat in response.json() ]

#### Private API

### GET /v1/me/getpermissions
def get_permissions(api_key: str, api_secret: str):
    base_url = 'https://api.bitflyer.com'
    endpoint = '/v1/me/getpermissions'
    
    return send_request(base_url, endpoint, method='GET', api_key=api_key, api_secret=api_secret)

class Permissions(BaseModel):
    items: list[str]

    @staticmethod
    def get(api_key: str, api_secret: str):
        response = get_permissions(api_key=api_key, api_secret=api_secret)
        response.raise_for_status()
        return Permissions(items=response.json())

### GET /v1/me/gettradingcommission
def get_tradingcommission(api_key: str, api_secret: str, product_code: str):
    base_url = 'https://api.bitflyer.com'
    endpoint = '/v1/me/gettradingcommission'
    
    params = {
        "product_code": product_code,
    }

    return send_request(base_url, endpoint, method='GET', params=params, api_key=api_key, api_secret=api_secret)

class TradingCommission(BaseModel):
    commission_rate: Fraction

    @validator('commission_rate', pre=True)
    def convert_to_fraction(cls, v):
        return Fraction(str(v))
    
    @staticmethod
    def get(api_key: str, api_secret: str, product_code: str):
        response = get_tradingcommission(api_key=api_key, api_secret=api_secret, product_code=product_code)
        response.raise_for_status()
        return TradingCommission(**response.json())

### GET /v1/me/getbalance
def get_balance(api_key: str, api_secret: str):
    base_url = 'https://api.bitflyer.com'
    endpoint = '/v1/me/getbalance'
    
    return send_request(base_url, endpoint, method='GET', api_key=api_key, api_secret=api_secret)

class Balance(BaseModel):
    currency_code: str
    amount: Fraction
    available: Fraction

    @validator('amount', 'available', pre=True)
    def convert_to_fraction(cls, v):
        return Fraction(str(v))

    @staticmethod
    def get(api_key: str, api_secret: str) -> list[Balance]:
        response = get_balance(api_key=api_key, api_secret=api_secret)
        response.raise_for_status()
        return [ Balance(**b) for b in response.json() ]

### GET /v1/me/getbalancehistory
def get_balancehistory(
        api_key: str,
        api_secret: str,
        currency_code: str='JPY',
        count: int=None,
        before: int=None,
        after: int=None):
    base_url = 'https://api.bitflyer.com'
    endpoint = '/v1/me/getbalancehistory'
    
    params = {
        "currency_code": currency_code,
    }

    if count is not None:
        params["count"] = str(count)
    if before is not None:
        params["before"] = str(before)
    if after is not None:
        params["after"] = str(after)

    return send_request(base_url, endpoint, method='GET', params=params, api_key=api_key, api_secret=api_secret)

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

    @validator(
        'price', 'amount', 'quantity', 'commission', 'balance',
        pre=True
    )
    def convert_to_fraction(cls, v):
        return Fraction(str(v))

    @staticmethod
    def get(
        api_key: str,
        api_secret: str,
        currency_code: str='JPY',
        count: int=None,
        before: int=None,
        after: int=None):
        response = get_balancehistory(
            api_key=api_key,
            api_secret=api_secret,
            currency_code=currency_code,
            count=count,
            before=before,
            after=after,
        )
        response.raise_for_status()
        return [ BalanceHistory(**bh) for bh in response.json() ]

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
        child_order_id: str=None,
        child_order_acceptance_id: str=None):
    base_url = 'https://api.bitflyer.com'
    endpoint = "/v1/me/cancelchildorder"

    if (child_order_id is None) and (child_order_acceptance_id is None):
        raise TypeError('child_order_id xor child_order_acceptance_id must be specified.')
    elif (child_order_id is not None) and (child_order_acceptance_id is not None):
        raise TypeError('child_order_id xor child_order_acceptance_id must be specified.')
    elif child_order_id is not None:
        body = {
            'product_code': product_code,
            'child_order_id': child_order_id,
        }
    elif child_order_acceptance_id is not None:
        body = {
            'product_code': product_code,
            'child_order_acceptance_id': child_order_acceptance_id,
        }
    else:
        raise RuntimeError('unknown error.')

    body = json.dumps(body)
    
    return send_request(base_url, endpoint, method='POST', body=body, api_key=api_key, api_secret=api_secret)

class ChildOrderResponse(BaseModel):
    # product_code は本来レスポンスに含まれないが、キャンセル時には必須パラメータなのでセットにしておく。
    product_code: str
    child_order_acceptance_id: str

    def send(self, api_key: str, api_secret: str):
        response = send_cancelchildorder(api_key=api_key, api_secret=api_secret, **self.model_dump())
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
        price: Optional[int]=None,
        size: float,
        minute_to_expire: int=43200,
        time_in_force: str='GTC'):
    base_url = 'https://api.bitflyer.com'
    endpoint = "/v1/me/sendchildorder"
    
    if child_order_type not in { 'LIMIT', 'MARKET' }:
        raise ValueError("")
    if side not in { 'BUY', 'SELL' }:
        raise ValueError("")
    
    body = {}
    body['product_code'] = product_code
    body['child_order_type'] = child_order_type  # 指値なら 'LIMIT', 成行なら 'MARKET'
    body['side'] = side  # 買いなら 'BUY', 売りなら 'SELL'
    if (child_order_type == 'LIMIT') and (price is None):
        raise ValueError("price must be specified when child_order_type == 'LIMIT'")
    elif (child_order_type == 'MARKET') and (price is None):
        # 成行注文でも price の指定は可能なようだが、どのような挙動になるかは不明。
        pass
    else:
        body['price'] = price  # 価格の指定
    body['size'] = size  # 注文数量
    body['minute_to_expire'] = minute_to_expire  # 期限切れまでの時間（分）
    body['time_in_force'] = time_in_force  # 執行数量条件

    body = json.dumps(body)
    
    return send_request(base_url, endpoint, method='POST', body=body, api_key=api_key, api_secret=api_secret)

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
        minute_to_expire: int=43200,
        time_in_force: str='GTC'):
        return ChildOrder(
            product_code=product_code,
            child_order_type=child_order_type,
            side='BUY',
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
        minute_to_expire: int=43200,
        time_in_force: str='GTC'):
        return ChildOrder(
            product_code=product_code,
            child_order_type=child_order_type,
            side='SELL',
            price=price,
            size=size,
            minute_to_expire=minute_to_expire,
            time_in_force=time_in_force,
        )
    
    @staticmethod
    def limit_buy(product_code: str, price: int, size: float, minute_to_expire: int=43200, time_in_force: str='GTC'):
        """指値注文
        """
        return ChildOrder(
            product_code=product_code,
            child_order_type='LIMIT',
            side='BUY',
            price=price,
            size=size,
            minute_to_expire=minute_to_expire,
            time_in_force=time_in_force,
        )

    @staticmethod
    def market_buy(product_code: str, size: float, minute_to_expire: int=43200, time_in_force: str='GTC'):
        """成行注文
        """
        return ChildOrder(
            product_code=product_code,
            child_order_type='MARKET',
            side='BUY',
            price=None,
            size=size,
            minute_to_expire=minute_to_expire,
            time_in_force=time_in_force,
        )
    
    @staticmethod
    def limit_sell(product_code: str, price: int, size: float, minute_to_expire: int=43200, time_in_force: str='GTC'):
        """指値注文
        """
        return ChildOrder(
            product_code=product_code,
            child_order_type='LIMIT',
            side='SELL',
            price=price,
            size=size,
            minute_to_expire=minute_to_expire,
            time_in_force=time_in_force,
        )
    
    @staticmethod
    def market_sell(product_code: str, size: float, minute_to_expire: int=43200, time_in_force: str='GTC'):
        """成行注文
        """
        return ChildOrder(
            product_code=product_code,
            child_order_type='MARKET',
            side='SELL',
            price=None,
            size=size,
            minute_to_expire=minute_to_expire,
            time_in_force=time_in_force,
        )

    def send(self, api_key: str, api_secret: str):
        response = send_childorder(api_key=api_key, api_secret=api_secret, **self.model_dump())
        response.raise_for_status()
        return ChildOrderResponse(
            product_code=self.product_code,
            **response.json()
        )

######## get_executions utils
import time
import datetime

def get_min_id_from_exec_list(xs: list):
    return min([ x['id'] for x in xs ])

def get_max_id_from_exec_list(xs: list):
    return max([ x['id'] for x in xs ])

def get_executions_backward(
        product_code: str='btc_jpy',
        count: int | str=None,
        before: int | str=None,
        after: int | str=None,
        max_iter: int=500) -> list:
    min_id = after
    max_id = before

    ret = []
    for _ in range(max_iter):
        response = get_executions(product_code=product_code, count=count, before=max_id, after=min_id)

        if response.status_code != requests.codes.ok:
            # 通信エラーや取得できる範囲を超えて取得した場合
            break

        exec_list = response.json()

        if len(exec_list) == 0:
            # before < after の関係になったなど、
            # 条件に一致する取引が存在しなくなった
            break

        # 取得したうちの最小の id が、次の最大の id となる。
        max_id = get_min_id_from_exec_list(exec_list)
        
        ret.append(response)

        # rate limit は 0.6 秒くらいなので
        # 安全マージンを入れて 1 秒
        time.sleep(1)
    
    return ret

def flatten_response_list(response_list):
    ret = []
    for resp in response_list:
        ret.extend(resp.json())
    return ret

def sort_exec_list_by_id(exec_list, reverse: bool=False):
    """
    id をキーとしてソートする関数

    :param data: ソート対象の辞書リスト
    :return: id の昇順でソートされたリスト
    """
    return sorted(exec_list, key=lambda x: x['id'], reverse=reverse)

def parse_exec_date(exec_date: str) -> datetime:
    if '.' in exec_date:
        # 2024-03-10T09:19:13.68
        dt = datetime.strptime(exec_date, '%Y-%m-%dT%H:%M:%S.%f')
    else:
        # 2024-03-10T09:19:13
        dt = datetime.strptime(exec_date, '%Y-%m-%dT%H:%M:%S')
    return dt

def convert_exec_list_to_table(exec_list: list):
    table = {}
    for exec in exec_list:
        dt = parse_exec_date(exec['exec_date'])
        key = dt.strftime('%Y-%m-%dT%H')
        if key not in table:
            table[key] = []
        table[key].append(exec)
    return table

def get_executions_as_table(
        product_code: str='btc_jpy',
        count: int | str=None,
        before: int | str=None,
        after: int | str=None,
        max_iter: int=500):
    
    response_list = get_executions_backward(
        product_code=product_code,
        count=count,
        before=before,
        after=after,
        max_iter=max_iter,
    )

    exec_table = convert_exec_list_to_table(
        sort_exec_list_by_id(
            flatten_response_list(response_list),
            reverse=False,
        )
    )

    return exec_table

######## utils for saving exec_list
import json
import gzip
import uuid
from pathlib import Path

def assign_unique_name_to_exec_list(exec_list: list,  dt: datetime, fstring: str='%Y%m%d-%H%M%S-%f'):
    xs = sort_exec_list_by_id(exec_list, reverse=False)

    min_id = xs[0]['id']
    max_id = xs[-1]['id']
    
    min_date = parse_exec_date(xs[0]['exec_date'])
    max_date = parse_exec_date(xs[-1]['exec_date'])
    
    return '_'.join([
        f"{min_id}",
        f"{max_id}",
        f"{min_date.strftime(fstring)}",
        f"{max_date.strftime(fstring)}",
        f"{dt.strftime(fstring)}",
        str(uuid.uuid4()),
    ])

def save_exec_list(exec_list: list, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

    with gzip.open(path, 'wb') as f:
        f.write(json.dumps(exec_list).encode('utf_8'))
    
    return path

########
import gzip
import requests
import time
import uuid

from datetime import datetime
from pathlib import Path
from typing import Callable
# from tqdm.auto import tqdm

def parse_event_date(event_date: str) -> datetime:
    if '.' in event_date:
        # 2024-03-10T09:19:13.68
        dt = datetime.strptime(event_date, '%Y-%m-%dT%H:%M:%S.%f')
    else:
        # 2024-03-10T09:19:13
        dt = datetime.strptime(event_date, '%Y-%m-%dT%H:%M:%S')
    return dt

def split_event_list(xs: list) -> dict[str, list]:
    table = {}
    for x in xs:
        day = x['event_date'].split('T')[0]
        if day not in table:
            table[day] = [x]
        else:
            table[day].append(x)
    return table

def sort_event_list_by_id(event_list: list) -> list:
    return sorted(event_list, reverse=True, key=lambda x: x['id'])

def parse_event_date(event_date: str) -> datetime:
    if '.' in event_date:
        # 2024-03-10T09:19:13.68
        dt = datetime.strptime(event_date, '%Y-%m-%dT%H:%M:%S.%f')
    else:
        # 2024-03-10T09:19:13
        dt = datetime.strptime(event_date, '%Y-%m-%dT%H:%M:%S')
    return dt

def get_event_log_name(event_list: list, dt: datetime, fstring: str='%Y%m%d-%H%M%S-%f') -> str:
    xs = sort_event_list_by_id(event_list)

    max_id = xs[0]['id']
    min_id = xs[-1]['id']
    
    max_date = parse_event_date(xs[0]['event_date'])
    min_date = parse_event_date(xs[-1]['event_date'])
    
    return '_'.join([
        f"{max_date.strftime(fstring)}",
        f"{min_date.strftime(fstring)}",
        f"{max_id}",
        f"{min_id}",
        f"{dt.strftime(fstring)}",
        str(uuid.uuid4()),
    ])

def get_min_id_from_event_list(xs: list):
    return min([ x['id'] for x in xs ])

########
# import pandas as pd
import uuid
from datetime import datetime


def get_exec_log_name(exec_list: list, dt: datetime, fstring: str='%Y%m%d-%H%M%S-%f') -> str:
    xs = sort_exec_list_by_id(exec_list)

    max_id = xs[0]['id']
    min_id = xs[-1]['id']
    
    max_date = parse_exec_date(xs[0]['exec_date'])
    min_date = parse_exec_date(xs[-1]['exec_date'])
    
    return '_'.join([
        f"{max_date.strftime(fstring)}",
        f"{min_date.strftime(fstring)}",
        f"{max_id}",
        f"{min_id}",
        f"{dt.strftime(fstring)}",
        str(uuid.uuid4()),
    ])

def exec_item_to_list(x: dict):
    return [ str(x[key]) for key in [
            'id', 'side', 'price', 'size', 'exec_date',
            'buy_child_order_acceptance_id',
            'sell_child_order_acceptance_id',
        ]
    ]

# def get_exec_table(exec_list: list) -> pd.DataFrame:
#     return pd.DataFrame([ exec_item_to_list(x) for x in exec_list ])

def is_id_in_exec_list(xs: list, id: int):
    return int(id) in { x['id'] for x in xs }

def get_exec_list_after(xs: list, id: int):
    ret = []
    for x in xs:
        if int(x['id']) <= id:
            break
        ret.append(x)
    return ret

def split_exec_list(xs: list) -> dict[str, list]:
    table = {}
    for x in xs:
        day = x['exec_date'].split('T')[0]
        if day not in table:
            table[day] = [x]
        else:
            table[day].append(x)
    return table

import gzip
import json
import requests
import time
from datetime import datetime
from pathlib import Path
from typing import Callable
# from tqdm.auto import tqdm

class Executions:
    def __init__(self, root_dir: Path, glob: str='**/*.json.gz', ignore: Callable[[Path], bool]='default'):
        self.root_dir = Path(root_dir)
        self._glob = glob

        ignore_set = {'__pycache__', '.ipynb_checkpoints'}

        if ignore is None:
            self.ignore = (lambda x: False)
        elif ignore == 'default':
            self.ignore = (lambda x: (len(set(x.parts) & ignore_set)) != 0)
        elif isinstance(ignore, set):
            ignore_set |= ignore
            self.ignore = (lambda x: (len(set(x.parts) & ignore_set)) != 0)
        elif isinstance(ignore, Callable):
            self.ignore = ignore
        else:
            raise TypeError(f"ignore must be one of (None, 'default', set[str], Callable[[Path], bool]).")
    
    def glob(self):
        return sorted([
            path for path in self.root_dir.glob(self._glob) 
                    if not self.ignore(path)
        ])

    @property
    def min_id(self):
        min_ids = [ int(path.stem.split('_')[3]) for path in self.glob() ]
        if len(min_ids) == 0:
            return None
        return min(min_ids)
    
    @property
    def max_id(self):
        max_ids = [ int(path.stem.split('_')[2]) for path in self.glob() ]
        if len(max_ids) == 0:
            return None
        return max(max_ids)
    
    def save(self, exec_list: list, dt: datetime=None) -> list[Path]:
        if len(exec_list) == 0:
            return []

        if dt is None:
            dt = datetime.now()
        
        exec_dict = split_exec_list(xs=exec_list)
        
        paths = []
        for _date, _xs in exec_dict.items():
            xs = sort_exec_list_by_id(_xs)
            name = get_exec_log_name(xs, dt)

            date = datetime.strptime(_date, '%Y-%m-%d')
            save_dir = self.root_dir / date.strftime('%Y') / date.strftime('%Y-%m') / date.strftime('%Y-%m-%d')
            path = (save_dir / name).with_suffix('.json.gz')        

            save_dir.mkdir(parents=True, exist_ok=True)

            with gzip.open(path, 'wb') as f:
                f.write(json.dumps(xs).encode('utf_8'))
            
            paths.append(path)
        
        return paths

    def read(self, path: Path):
        path = Path(path)

        with gzip.open(path, 'rb') as f:
            xs = f.read()

        return json.loads(xs.decode('utf-8'))

    def get_executions(self, mode: str='forward', max_iter: int=1000, before: int=None, after: int=None):
        if mode not in { 'forward', 'backward' }:
            raise ValueError('Undefined mode.')
        
        # １回目の取得設定
        if mode == 'backward':
            before = before if before is not None else self.min_id
            after = after
        elif mode == 'forward':
            before = before
            after = after if after is not None else self.max_id

        ret = []
        for _ in tqdm(range(max_iter)):
            now = datetime.now()
            
            resp = get_executions(count=500, before=before, after=after)
            
            if resp.status_code != requests.codes.ok:
                print(f"Error: {resp.status_code}")
                print(resp.content.decode('utf-8'))
                break

            xs = resp.json()
            paths = self.save(xs, now)
        
            if len(paths) == 0:
                print(f"All available executions have been retrieved.")
                break
            
            ret.extend(paths)

            # ２回目以降の取得設定
            # get_executions の挙動的に遡る方向（backward）でしか取得できないので、
            # backward, forward 問わず before のみ更新する
            before = get_min_id_from_exec_list(xs)

            # rate limit は 0.6 秒くらいなので
            # 安全マージンを入れて 1 秒
            time.sleep(1)
        
        return ret

# # def order_cancel(self):
# #     base_url = 'https://api.bitflyer.com'
# #     endpoint = "/v1/me/cancelchildorder"

# #     body = {
# #         "product_code": 'btc_jpy',
# #         "child_order_acceptance_id": "JRF20150707-033333-099999"
# #     }

# #     body = json.dumps(body)
# #     headers = self.header('POST', endpoint=endpoint, body=body)

# #     response = requests.post(base_url + endpoint, data=body, headers=headers)
# #     return response.status_code

# # def all_order_cancel():
# #     base_url = 'https://api.bitflyer.com'
# #     endpoint = "/v1/me/cancelallchildorders"

# #     body = {
# #         "product_code": 'btc_jpy'
# #     }

# #     body = json.dumps(body)
# #     headers = self.header('POST', endpoint=endpoint, body=body)

# #     response = requests.post(base_url + endpoint, data=body, headers=headers)
# #     return response.status_code

# def cashflow_to_history(df):
#     normalized_column = ['t', 'id', 'from', 'X(t)', 'to', 'Y(t+dt)', 'R(yt/xt)']

#     df = df.dropna(subset='product_code')

#     df_buy = df[df['trade_type'] == 'BUY']
#     df_sell = df[df['trade_type'] == 'SELL']

#     df_other = df[~df['trade_type'].isin({'BUY', 'SELL'})]
    
#     buy_his = df_buy[['trade_date', 'id', 'code_x', 'X(t)', 'code_y', 'Y(t+dt)']].copy()
#     buy_his['R(yt/xt)'] = buy_his['Y(t+dt)'] / buy_his['X(t)']
#     buy_his.columns = normalized_column
    
#     sell_his = df_sell[['trade_date', 'id', 'code_y', 'Y(t)', 'code_x', 'X(t+dt)']].copy()
#     sell_his['R(yt/xt)'] = sell_his['X(t+dt)'] / sell_his['Y(t)']
#     sell_his.columns = normalized_column

#     other_his = df_other[['trade_date', 'id', 'code_x', 'X(t)', 'code_x', 'X(t+dt)']].copy()
#     other_his['R(yt/xt)'] = 0
#     other_his.columns = normalized_column

#     ret = pd.concat([buy_his, sell_his, other_his], axis=0).sort_values('t', ascending=True).reset_index(drop=True)

#     return History(ret)

# class BitflyerAPI(TraderAPI):
#     @staticmethod
#     def make_code_pair_string(base: Union[str, CodePair], quote: Optional[str]=None) -> str:
#         if isinstance(base, str):
#             return f"{base.upper()}_{quote.upper()}"
#         elif isinstance(base, CodePair):
#             return f"{base.base.upper()}_{base.quote.upper()}"
#         raise TypeError("unrecognized type arguments")

#     def __init__(self, api_key, api_secret):
#         self._api_key = api_key
#         self._api_secret = api_secret
    
#     @property
#     def api_key(self):
#         return self._api_key
    
#     @property
#     def api_secret(self):
#         return self._api_secret

#     def __repr__(self):
#         if self.api_key == '[frozen]' and self.api_secret == '[frozen]':
#             return f"BitflyerAPI(api_key='{self.api_key}', " + \
#                 f"api_secret='{self.api_secret}')"
#         return f"BitflyerAPI(api_key='{self.api_key[:4]}...', " + \
#             f"api_secret='{self.api_secret[:4]}...')"

#     def freeze(self):
#         return BitflyerAPI(api_key='[frozen]', api_secret='[frozen]')

#     def minimum_order_quantity(self, code_pair, t=None):
#         code = code_pair.base

#         qs = {
#             'BTC': BTC('0.001')
#         }
#         return qs[code]
    
#     def maximum_order_quantity(self, code_pair, t=None):
#         code = code_pair.base

#         qs = {
#             'BTC': BTC('1000')
#         }
#         return qs[code]

#     def get_commission(self, code_pair):
#         product_code = self.make_code_pair_string(code_pair)
        
#         try:
#             response = get_commission(self.api_key, self.api_secret, product_code)
#             response.raise_for_status()
#         except RequestException as e:
#             print(e)
#             response = None
            
#         resp = response.json()
        
#         return Fraction(str(resp['commission_rate']))
    
#     def get_ticker(self, code_pair, t=None):
#         product_code = self.make_code_pair_string(code_pair)

#         try:
#             response = get_ticker(product_code=product_code)
#             response.raise_for_status()
#         except RequestException as e:
#             print(e)
#             response = None
        
#         return response.json()

#     def get_best_bid(self, code_pair, t=None):
#         ticker = self.get_ticker(code_pair, t=t)
        
#         # 買い値
#         bid_rate = Rate(from_code='BTC', to_code='JPY', r=str(ticker['best_bid']))
        
#         return bid_rate
    
#     def get_best_ask(self, code_pair, t=None):
#         ticker = self.get_ticker(code_pair, t=t)

#         # 売り値
#         ask_rate = Rate(from_code='BTC', to_code='JPY', r=str(ticker['best_ask']))
        
#         return ask_rate

#     def buy(self, size, t=None, wallet=None, history=None):
#         try:
#             response = order(self.api_key, self.api_secret, 'BUY', 'MARKET', 0, size)
#             response.raise_for_status()
#         except RequestException as e:
#             print(e)
#             print(response)
#             response = None
        
#         return response.json()
    
#     def sell(self, size, t=None, wallet=None, history=None):
#         try:
#             response = order(self.api_key, self.api_secret, 'SELL', 'MARKET', 0, size)
#             response.raise_for_status()
#         except RequestException as e:
#             print(e)
#             print(response)
#             response = None
        
#         return response.json()

#     def download_wallet(self):
#         response = get_balance(self.api_key, self.api_secret)
#         response.raise_for_status()
            
#         stocks = response.json()
        
#         w = Wallet()
#         for stock in stocks:
#             w.add(Stock(stock['currency_code'], str(stock['available'])))

#         return w
    
#     def get_balance_history(self, currency_code='JPY'):
#         """
#         Response の内訳は以下。
#         id ... 注文のイベントに結びついたID（と思われる）
#         trade_date ... 取引が成立した時間（と思われる）
#         event_date ... イベントが受け付けられた時間（と思われる、trade_date と同じ値が入っている）
#         product_code ... その取引における通貨のペア
#         currency_code ... 所持しているどの通貨に関する情報か
#         trade_type ... BUY, SELL, DEPOSIT, あとおそらく WITHDRAW がある
#                        currency_code を基準とした trade の type なので、
#                        currency_code='JPY', trade_type='sell' ならば、
#                        日本円を売って product_code の商品を買ったことを意味する
#         price ... その時点での商品の値段
#         amount ... 取引した currency_code の通貨の量
#         quantity ... 取引した product_code の商品の量
#         commission ... 取引手数料。あくまでも currency_code の通貨から引かれた量であり、
#                        Bitflyer は手数料は BTC から引くので JPY の履歴には手数料の記録は残らない。
#         balance ... 取引前に所持していた currency_code の通貨の量
#         order_id ... 取引に結びついたID（と思われる）
#                      たとえば１回の注文の成立に２回の取引が必要になったとき、
#                      おそらくその２回の取引について order_id は一致する。
#         """
#         response = get_balance_history(self.api_key, self.api_secret, currency_code=currency_code)
#         return response 
    
#     def get_cashflow(self, t=None):
#         # DEPOSIT と WITHDRAW も考慮したい
#         df_jpy = pd.DataFrame.from_dict(self.get_balance_history(currency_code='JPY').json())
#         df_btc = pd.DataFrame.from_dict(self.get_balance_history(currency_code='BTC').json())
        
#         meta_columns = ['order_id', 'trade_date', 'product_code', 'trade_type']
#         cash_columns = ['balance', 'amount', 'commission']
#         x_columns = ['x(t)', 'X(t)', 'commission_x']
#         y_columns = ['y(t)', 'Y(t)', 'commission_y']
#         all_columns = ['id'] + meta_columns + \
#             ['code_x', 'code_y', 'x(t)', 'y(t)', 'X(t)', 'Y(t)', 'X(t+dt)', 'Y(t+dt)', 'commission_x', 'commission_y']
        
#         # id, 日付など
#         df_meta = df_jpy[['id'] + meta_columns].copy()
#         df_meta['trade_date'] = df_meta['trade_date'].apply(lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S.%f'))
        
#         # quote（BTC_JPY で言えば JPY）の残高や取引金額などの情報
#         df_x = df_jpy[['id'] + cash_columns].copy()
#         df_x.columns = ['id'] + x_columns
        
#         # お金に関しては数値誤差を防ぐためいったん有理数へ変換
#         df_x[x_columns] = df_x[x_columns].applymap(lambda x: Fraction(str(x)))
#         # 取引金額に手数料を加算（手数料は負の値で格納されている）
#         df_x['X(t)'] += df_x['commission_x']
#         # X(t) はもともと amount（取引金額）なので、正の金額なら取引後に増加、負の値なら減少
#         df_x['X(t+dt)'] = df_x['X(t)'].apply(lambda x: x if x >= 0 else Fraction(0))
#         df_x['X(t)'] = df_x['X(t)'].apply(lambda x: -x if x < 0 else Fraction(0))
#         df_x['code_x'] = df_jpy['currency_code']
        
#         # base（BTC_JPY で言えば BTC）についても同様に処理
#         df_y = df_btc[['id'] + cash_columns].copy()
#         df_y.columns = ['id'] + y_columns

#         df_y[y_columns] = df_y[y_columns].applymap(lambda y: Fraction(str(y)))
#         df_y['Y(t)'] += df_y['commission_y']
#         df_y['Y(t+dt)'] = df_y['Y(t)'].apply(lambda y: y if y >= 0 else Fraction(0))
#         df_y['Y(t)'] = df_y['Y(t)'].apply(lambda y: -y if y < 0 else Fraction(0))
#         df_y['code_y'] = df_btc['currency_code']
        
#         df_xy = pd.merge(df_x, df_y, left_on='id', right_on='id', how='outer')
#         df_all = pd.merge(df_meta, df_xy, left_on='id', right_on='id', how='outer')
        
#         df_ret = df_all[all_columns]
        
#         return focus(df_ret, t, column='trade_date')
    
#     def download_history(self, t=None):
#         df = self.get_cashflow(t=t)
#         return cashflow_to_history(df)