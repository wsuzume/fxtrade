import json
import requests
import warnings

import numpy as np
import pandas as pd

from datetime import datetime
from glob import glob
from pathlib import Path

import hashlib
import hmac
import requests
import time
from urllib.parse import urljoin

from fractions import Fraction

from requests.exceptions import RequestException

from typing import Union, Optional

from ..api import CodePair, TraderAPI
from ..trade import Trade
from ..history import History
from ..stock import Stock, Rate
from ..stocks import JPY, BTC
from ..wallet import Wallet
from ..utils import focus

def build_headers(api_key: str, api_secret: str, method: str, endpoint: str, body: str=None) -> dict:
    timestamp = str(time.time())
    
    if body is None:
        message = timestamp + method + endpoint
    else:
        message = timestamp + method + endpoint + body
        
    signature = hmac.new(api_secret.encode('utf-8'), message.encode('utf-8'),
                         digestmod=hashlib.sha256).hexdigest()
    
    headers = {
        'Content-Type': 'application/json',
        'ACCESS-KEY': api_key,
        'ACCESS-TIMESTAMP': timestamp,
        'ACCESS-SIGN': signature
    }
    
    return headers

def query_string(params):
    return '&'.join([ str(k) + '=' + str(v) for k, v in params.items() ])

def send_request(base_url, endpoint, method='GET', body=None, params=None, api_key=None, api_secret=None):
    url = urljoin(base_url, endpoint)
    
    func = {
        'GET': requests.get,
        'POST': requests.post,
    }
    
    if params is not None:
        endpoint = endpoint + '?' + query_string(params)
    
    if api_key is None:
        return func[method](url, data=body, params=params)
    else:
        headers = build_headers(api_key, api_secret, method, endpoint=endpoint, body=body)
        return func[method](url, headers=headers, data=body, params=params)

def get_balance(api_key, api_secret):
    base_url = 'https://api.bitflyer.com'
    endpoint = '/v1/me/getbalance'
    
    return send_request(base_url, endpoint, method='GET', api_key=api_key, api_secret=api_secret)

def get_balance_history(api_key, api_secret, currency_code='JPY'):
    base_url = 'https://api.bitflyer.com'
    endpoint = '/v1/me/getbalancehistory'
    
    params = {
        "currency_code": currency_code,
        "count": str(100),
    }

    return send_request(base_url, endpoint, method='GET', params=params, api_key=api_key, api_secret=api_secret)

def get_commission(api_key, api_secret, product_code):
    base_url = 'https://api.bitflyer.com'
    endpoint = '/v1/me/gettradingcommission'
    
    params = {
        "product_code": product_code,
    }

    return send_request(base_url, endpoint, method='GET', params=params, api_key=api_key, api_secret=api_secret)

def get_ticker(product_code='btc_jpy'):
    base_url = 'https://api.bitflyer.com'
    endpoint = '/v1/ticker'
    
    params = {
        "product_code": product_code,
    }
    
    return send_request(base_url, endpoint, params=params)

# # def get_child_orders(api_key, api_secret, product_code='btc_jpy'):
# #     base_url = 'https://api.bitflyer.com'
# #     endpoint = '/v1/me/getchildorders'
    
# #     params = {
# #         "product_code": product_code,
# #         "count": str(100),
# #     }

# #     return send_request(base_url, endpoint, method='GET', params=params, api_key=api_key, api_secret=api_secret)

def order(api_key, api_secret, side: str, order_type: str, price: int, size: float, expire: int=1000):
    if side not in { 'BUY', 'SELL' }:
        raise ValueError("")
    
    if order_type not in { 'LIMIT', 'MARKET' }:
        raise ValueError("")
    
    base_url = 'https://api.bitflyer.com'
    endpoint = "/v1/me/sendchildorder"
    
    body = {
        "product_code": 'btc_jpy',  # ビットコイン（日本円）
        "child_order_type": order_type,  # 指値。成行きの場合は、MARKET
        "side": side,  # 「買い」注文
        #"price": price,  # 価格指定
        "size": size,  # 注文数量
        "minute_to_expire": expire,  # 期限切れまでの時間（分）
        "time_in_force": 'GTC'  # GTC発注
    }

    body = json.dumps(body)
    
    return send_request(base_url, endpoint, method='POST', body=body, api_key=api_key, api_secret=api_secret)
    
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

def cashflow_to_history(df):
    normalized_column = ['t', 'id', 'from', 'X(t)', 'to', 'Y(t+dt)', 'R(yt/xt)']

    df = df.dropna(subset='product_code')

    df_buy = df[df['trade_type'] == 'BUY']
    df_sell = df[df['trade_type'] == 'SELL']

    df_other = df[~df['trade_type'].isin({'BUY', 'SELL'})]
    
    buy_his = df_buy[['trade_date', 'id', 'code_x', 'X(t)', 'code_y', 'Y(t+dt)']].copy()
    buy_his['R(yt/xt)'] = buy_his['Y(t+dt)'] / buy_his['X(t)']
    buy_his.columns = normalized_column
    
    sell_his = df_sell[['trade_date', 'id', 'code_y', 'Y(t)', 'code_x', 'X(t+dt)']].copy()
    sell_his['R(yt/xt)'] = sell_his['X(t+dt)'] / sell_his['Y(t)']
    sell_his.columns = normalized_column

    other_his = df_other[['trade_date', 'id', 'code_x', 'X(t)', 'code_x', 'X(t+dt)']].copy()
    other_his['R(yt/xt)'] = 0
    other_his.columns = normalized_column

    ret = pd.concat([buy_his, sell_his, other_his], axis=0).sort_values('t', ascending=True).reset_index(drop=True)

    return History(ret)

class BitflyerAPI(TraderAPI):
    @staticmethod
    def make_code_pair_string(base: Union[str, CodePair], quote: Optional[str]=None) -> str:
        if isinstance(base, str):
            return f"{base.upper()}_{quote.upper()}"
        elif isinstance(base, CodePair):
            return f"{base.base.upper()}_{base.quote.upper()}"
        raise TypeError("unrecognized type arguments")

    def __init__(self, api_key, api_secret):
        self._api_key = api_key
        self._api_secret = api_secret
    
    @property
    def api_key(self):
        return self._api_key
    
    @property
    def api_secret(self):
        return self._api_secret

    def __repr__(self):
        if self.api_key == '[frozen]' and self.api_secret == '[frozen]':
            return f"BitflyerAPI(api_key='{self.api_key}', " + \
                f"api_secret='{self.api_secret}')"
        return f"BitflyerAPI(api_key='{self.api_key[:4]}...', " + \
            f"api_secret='{self.api_secret[:4]}...')"

    def freeze(self):
        return BitflyerAPI(api_key='[frozen]', api_secret='[frozen]')

    def minimum_order_quantity(self, code_pair, t=None):
        code = code_pair.base

        qs = {
            'BTC': BTC('0.001')
        }
        return qs[code]
    
    def maximum_order_quantity(self, code_pair, t=None):
        code = code_pair.base

        qs = {
            'BTC': BTC('1000')
        }
        return qs[code]

    def get_commission(self, code_pair):
        product_code = self.make_code_pair_string(code_pair)
        
        try:
            response = get_commission(self.api_key, self.api_secret, product_code)
            response.raise_for_status()
        except RequestException as e:
            print(e)
            response = None
            
        resp = response.json()
        
        return Fraction(str(resp['commission_rate']))
    
    def get_ticker(self, code_pair, t=None):
        product_code = self.make_code_pair_string(code_pair)

        try:
            response = get_ticker(product_code=product_code)
            response.raise_for_status()
        except RequestException as e:
            print(e)
            response = None
        
        return response.json()

    def get_best_bid(self, code_pair, t=None):
        ticker = self.get_ticker(code_pair, t=t)
        
        # 買い値
        bid_rate = Rate(from_code='BTC', to_code='JPY', r=str(ticker['best_bid']))
        
        return bid_rate
    
    def get_best_ask(self, code_pair, t=None):
        ticker = self.get_ticker(code_pair, t=t)

        # 売り値
        ask_rate = Rate(from_code='BTC', to_code='JPY', r=str(ticker['best_ask']))
        
        return ask_rate

    def buy(self, size, t=None, history=None):
        try:
            response = order(self.api_key, self.api_secret, 'BUY', 'MARKET', 0, size)
            response.raise_for_status()
        except RequestException as e:
            print(e)
            print(response)
            response = None
        
        return response.json()
    
    def sell(self, size, t=None, history=None):
        try:
            response = order(self.api_key, self.api_secret, 'SELL', 'MARKET', 0, size)
            response.raise_for_status()
        except RequestException as e:
            print(e)
            print(response)
            response = None
        
        return response.json()

    def download_wallet(self):
        response = get_balance(self.api_key, self.api_secret)
        response.raise_for_status()
            
        stocks = response.json()
        
        w = Wallet()
        for stock in stocks:
            w.add(Stock(stock['currency_code'], str(stock['available'])))

        return w
    
    def get_balance_history(self, currency_code='JPY'):
        """
        Response の内訳は以下。
        id ... 注文のイベントに結びついたID（と思われる）
        trade_date ... 取引が成立した時間（と思われる）
        event_date ... イベントが受け付けられた時間（と思われる、trade_date と同じ値が入っている）
        product_code ... その取引における通貨のペア
        currency_code ... 所持しているどの通貨に関する情報か
        trade_type ... BUY, SELL, DEPOSIT, あとおそらく WITHDRAW がある
                       currency_code を基準とした trade の type なので、
                       currency_code='JPY', trade_type='sell' ならば、
                       日本円を売って product_code の商品を買ったことを意味する
        price ... その時点での商品の値段
        amount ... 取引した currency_code の通貨の量
        quantity ... 取引した product_code の商品の量
        commission ... 取引手数料。あくまでも currency_code の通貨から引かれた量であり、
                       Bitflyer は手数料は BTC から引くので JPY の履歴には手数料の記録は残らない。
        balance ... 取引前に所持していた currency_code の通貨の量
        order_id ... 取引に結びついたID（と思われる）
                     たとえば１回の注文の成立に２回の取引が必要になったとき、
                     おそらくその２回の取引について order_id は一致する。
        """
        response = get_balance_history(self.api_key, self.api_secret, currency_code=currency_code)
        return response 
    
    def get_cashflow(self, t=None):
        # DEPOSIT と WITHDRAW も考慮したい
        df_jpy = pd.DataFrame.from_dict(self.get_balance_history(currency_code='JPY').json())
        df_btc = pd.DataFrame.from_dict(self.get_balance_history(currency_code='BTC').json())
        
        meta_columns = ['order_id', 'trade_date', 'product_code', 'trade_type']
        cash_columns = ['balance', 'amount', 'commission']
        x_columns = ['x(t)', 'X(t)', 'commission_x']
        y_columns = ['y(t)', 'Y(t)', 'commission_y']
        all_columns = ['id'] + meta_columns + \
            ['code_x', 'code_y', 'x(t)', 'y(t)', 'X(t)', 'Y(t)', 'X(t+dt)', 'Y(t+dt)', 'commission_x', 'commission_y']
        
        # id, 日付など
        df_meta = df_jpy[['id'] + meta_columns].copy()
        df_meta['trade_date'] = df_meta['trade_date'].apply(lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S.%f'))
        
        # quote（BTC_JPY で言えば JPY）の残高や取引金額などの情報
        df_x = df_jpy[['id'] + cash_columns].copy()
        df_x.columns = ['id'] + x_columns
        
        # お金に関しては数値誤差を防ぐためいったん有理数へ変換
        df_x[x_columns] = df_x[x_columns].applymap(lambda x: Fraction(str(x)))
        # 取引金額に手数料を加算（手数料は負の値で格納されている）
        df_x['X(t)'] += df_x['commission_x']
        # X(t) はもともと amount（取引金額）なので、正の金額なら取引後に増加、負の値なら減少
        df_x['X(t+dt)'] = df_x['X(t)'].apply(lambda x: x if x >= 0 else Fraction(0))
        df_x['X(t)'] = df_x['X(t)'].apply(lambda x: -x if x < 0 else Fraction(0))
        df_x['code_x'] = df_jpy['currency_code']
        
        # base（BTC_JPY で言えば BTC）についても同様に処理
        df_y = df_btc[['id'] + cash_columns].copy()
        df_y.columns = ['id'] + y_columns

        df_y[y_columns] = df_y[y_columns].applymap(lambda y: Fraction(str(y)))
        df_y['Y(t)'] += df_y['commission_y']
        df_y['Y(t+dt)'] = df_y['Y(t)'].apply(lambda y: y if y >= 0 else Fraction(0))
        df_y['Y(t)'] = df_y['Y(t)'].apply(lambda y: -y if y < 0 else Fraction(0))
        df_y['code_y'] = df_btc['currency_code']
        
        df_xy = pd.merge(df_x, df_y, left_on='id', right_on='id', how='outer')
        df_all = pd.merge(df_meta, df_xy, left_on='id', right_on='id', how='outer')
        
        df_ret = df_all[all_columns]
        
        return focus(df_ret, t, column='trade_date')
    
    def download_history(self, t=None):
        df = self.get_cashflow(t=t)
        return cashflow_to_history(df)