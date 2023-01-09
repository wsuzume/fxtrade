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

from ..api import CodePair, TradeAPI
from ..trade import Transfer, Trade, History
from ..stock import Stock, Rate
from ..stocks import JPY, BTC
from ..wallet import Wallet

# # def build_headers(api_key: str, api_secret: str, method: str, endpoint: str, body: str='') -> dict:
# #     timestamp = str(time.time())
    
# #     if body is None:
# #         message = timestamp + method + endpoint
# #     else:
# #         message = timestamp + method + endpoint + body
        
# #     signature = hmac.new(api_secret.encode('utf-8'), message.encode('utf-8'),
# #                          digestmod=hashlib.sha256).hexdigest()
    
# #     headers = {
# #         'Content-Type': 'application/json',
# #         'ACCESS-KEY': api_key,
# #         'ACCESS-TIMESTAMP': timestamp,
# #         'ACCESS-SIGN': signature
# #     }
    
# #     return headers

# # def query_string(params):
# #     return '&'.join([ str(k) + '=' + str(v) for k, v in params.items() ])

# # def send_request(base_url, endpoint, method='GET', body=None, params=None, api_key=None, api_secret=None):
# #     url = urljoin(base_url, endpoint)
    
# #     func = {
# #         'GET': requests.get,
# #         'POST': requests.post,
# #     }
    
# #     if params is not None:
# #         endpoint = endpoint + '?' + query_string(params)
    
# #     if api_key is None:
# #         return func[method](url, data=body, params=params)
# #     else:
# #         headers = build_headers(api_key, api_secret, method, endpoint=endpoint, body=body)
# #         return func[method](url, headers=headers, data=body, params=params)

# # def get_balance(api_key, api_secret):
# #     base_url = 'https://api.bitflyer.com'
# #     endpoint = '/v1/me/getbalance'
    
# #     return send_request(base_url, endpoint, method='GET', api_key=api_key, api_secret=api_secret)

# # def get_balance_history(api_key, api_secret, currency_code='JPY'):
# #     base_url = 'https://api.bitflyer.com'
# #     endpoint = '/v1/me/getbalancehistory'
    
# #     params = {
# #         "currency_code": currency_code,
# #         "count": str(100),
# #     }

# #     return send_request(base_url, endpoint, method='GET', params=params, api_key=api_key, api_secret=api_secret)

# # def get_ticker(product_code='btc_jpy'):
# #     base_url = 'https://api.bitflyer.com'
# #     endpoint = '/v1/ticker'
    
# #     params = {
# #         "product_code": product_code,
# #     }
    
# #     return send_request(base_url, endpoint, params=params)

# # def get_commission(api_key, api_secret, product_code):
# #     base_url = 'https://api.bitflyer.com'
# #     endpoint = '/v1/me/gettradingcommission'
    
# #     params = {
# #         "product_code": product_code,
# #     }

# #     return send_request(base_url, endpoint, method='GET', params=params, api_key=api_key, api_secret=api_secret)

# # def get_child_orders(api_key, api_secret, product_code='btc_jpy'):
# #     base_url = 'https://api.bitflyer.com'
# #     endpoint = '/v1/me/getchildorders'
    
# #     params = {
# #         "product_code": product_code,
# #         "count": str(100),
# #     }

# #     return send_request(base_url, endpoint, method='GET', params=params, api_key=api_key, api_secret=api_secret)

# # def order(api_key, api_secret, side: str, order_type: str, price: int, size: float, expire: int=1000):
# #     if side not in { 'BUY', 'SELL' }:
# #         raise ValueError("")
    
# #     if order_type not in { 'LIMIT', 'MARKET' }:
# #         raise ValueError("")
    
# #     base_url = 'https://api.bitflyer.com'
# #     endpoint = "/v1/me/sendchildorder"
    
# #     body = {
# #         "product_code": 'btc_jpy',  # ビットコイン（日本円）
# #         "child_order_type": order_type,  # 指値。成行きの場合は、MARKET
# #         "side": side,  # 「買い」注文
# #         #"price": price,  # 価格指定
# #         "size": size,  # 注文数量
# #         "minute_to_expire": expire,  # 期限切れまでの時間（分）
# #         "time_in_force": 'GTC'  # GTC発注
# #     }

# #     body = json.dumps(body)
    
# #     return send_request(base_url, endpoint, method='POST', body=body, api_key=api_key, api_secret=api_secret)
    
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

# # def cashflow_to_history(df):
# #     df_buy = df[df['trade_type'] == 'BUY']
# #     df_sell = df[df['trade_type'] == 'SELL']
    
# #     buy_his = df_buy[['trade_date', 'order_id', 'code_x', 'X(t)', 'code_y', 'Y(t+dt)']].copy()
# #     buy_his['R(yt/xt)'] = buy_his['Y(t+dt)'] / buy_his['X(t)']
# #     buy_his.columns = ['t', 'order_id', 'from', 'X(t)', 'to', 'Y(t+dt)', 'R(yt/xt)']
    
# #     sell_his = df_sell[['trade_date', 'order_id', 'code_y', 'Y(t)', 'code_x', 'X(t+dt)']].copy()
# #     sell_his['R(yt/xt)'] = sell_his['X(t+dt)'] / sell_his['Y(t)']
# #     sell_his.columns = ['t', 'order_id', 'from', 'X(t)', 'to', 'Y(t+dt)', 'R(yt/xt)']
    
# #     ret = pd.concat([buy_his, sell_his], axis=0).sort_values('t', ascending=False).reset_index(drop=True)

# #     return History(ret)

class BitflyerAPI(TradeAPI):
    # @staticmethod
    # def make_ticker(from_code, to_code):
    #     return f"{from_code}_{to_code}"
    
    # @staticmethod
    # def make_code_pair(pair):
    #     return f"{pair.terminal}_{pair.initial}"

    @staticmethod
    def make_code_pair_string(base: Union[str, CodePair], quote: Optional[str]=None) -> str:
        if isinstance(base, str):
            return f"{base.upper()}_{quote.upper()}"
        elif isinstance(base, CodePair):
            return f"{base.base.upper()}_{base.quote.upper()}"
        raise TypeError("unrecognized type arguments")

    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
    
    def __repr__(self):
        return f"BitflyerAPI(api_key='{self.api_key[:4]}...', " + \
            f"api_secret='{self.api_secret[:4]}...')"

# #     def minimum_order_quantity(self, code):
# #         qs = {
# #             'BTC': BTC('0.001')
# #         }
# #         return qs[code]
    
# #     def maximum_order_quantity(self, code):
# #         qs = {
# #             'BTC': BTC('1000')
# #         }
# #         return qs[code]
    
# #     def get_commission(self, product_code=None):
# #         if product_code is None:
# #             product_code = 'BTC_JPY'
        
# #         try:
# #             response = get_commission(self.api_key, self.api_secret, product_code)
# #             response.raise_for_status()
# #         except RequestException as e:
# #             print(e)
# #             response = None
            
# #         resp = response.json()
        
# #         return Fraction(str(resp['commission_rate']))
    
# #     def get_ticker(self, code, t=None):
# #         if code is None:
# #             code = 'btc_jpy'
        
# #         try:
# #             response = get_ticker(product_code=code)
# #             response.raise_for_status()
# #         except RequestException as e:
# #             print(e)
# #             response = None
        
# #         return response.json()
    
# #     def get_best_bid(self, code):
# #         ticker = self.get_ticker(code=code)
        
# #         # 買い値
# #         bid_rate = Rate(from_code='BTC', to_code='JPY', r=str(ticker['best_bid']))
        
# #         return bid_rate
    
# #     def get_best_ask(self, code):
# #         ticker = self.get_ticker(code=code)

# #         # 売り値
# #         ask_rate = Rate(from_code='BTC', to_code='JPY', r=str(ticker['best_ask']))
        
# #         return ask_rate
    
# #     def get_balance(self):
# #         try:
# #             response = get_balance(self.api_key, self.api_secret)
# #             response.raise_for_status()
# #         except RequestException as e:
# #             print(e)
# #             response = None
            
# #         stocks = response.json()
        
# #         w = Wallet()
# #         for stock in stocks:
# #             w.add(Stock(stock['currency_code'], str(stock['available'])))
# #         return w
        
# #     def get_balance_history(self, currency_code='JPY'):
# #         try:
# #             response = get_balance_history(self.api_key, self.api_secret, currency_code=currency_code)
# #             response.raise_for_status()
# #         except RequestException as e:
# #             print(e)
# #             response = None
# #         return response.json()
    
# #     def get_cashflow(self, start_date=None):
# #         df_jpy = pd.DataFrame.from_dict(self.get_balance_history(currency_code='JPY'))
# #         df_btc = pd.DataFrame.from_dict(self.get_balance_history(currency_code='BTC'))
        
# #         meta_columns = ['order_id', 'trade_date', 'product_code', 'trade_type']
# #         cash_columns = ['balance', 'amount', 'commission']
# #         x_columns = ['x(t)', 'X(t)', 'commission_x']
# #         y_columns = ['y(t)', 'Y(t)', 'commission_y']
# #         all_columns = ['id'] + meta_columns + \
# #             ['code_x', 'code_y', 'x(t)', 'y(t)', 'X(t)', 'Y(t)', 'X(t+dt)', 'Y(t+dt)', 'commission_x', 'commission_y']
        
# #         df_meta = df_jpy[['id'] + meta_columns].copy()
# #         df_meta['trade_date'] = df_meta['trade_date'].apply(lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S.%f'))
        
# #         df_x = df_jpy[['id'] + cash_columns].copy()
# #         df_x.columns = ['id'] + x_columns
        
# #         df_x[x_columns] = df_x[x_columns].applymap(lambda x: Fraction(str(x)))
# #         df_x['X(t)'] += df_x['commission_x']
# #         df_x['X(t+dt)'] = df_x['X(t)'].apply(lambda x: 0.0 if x < 0 else x)
# #         df_x['X(t)'] = df_x['X(t)'].apply(lambda x: -x if x < 0 else 0.0)
# #         df_x['code_x'] = df_jpy['currency_code']
        
# #         df_y = df_btc[['id'] + cash_columns].copy()
# #         df_y.columns = ['id'] + y_columns
# #         df_y[y_columns] = df_y[y_columns].applymap(lambda x: Fraction(str(x)))
# #         df_y['Y(t)'] += df_y['commission_y']
# #         df_y['Y(t+dt)'] = df_y['Y(t)'].apply(lambda y: 0.0 if y < 0 else y)
# #         df_y['Y(t)'] = df_y['Y(t)'].apply(lambda y: -y if y < 0 else 0.0)
# #         df_y['code_y'] = df_btc['currency_code']
        
# #         df_xy = pd.merge(df_x, df_y, left_on='id', right_on='id', how='outer')
# #         df_all = pd.merge(df_meta, df_xy, left_on='id', right_on='id', how='outer')
        
# #         df_ret = df_all[all_columns]
# #         if isinstance(start_date, datetime):
# #             df_ret = df_ret[df_ret['trade_date'] >= start_date]
        
# #         return df_ret.copy()
    
# #     def get_history(self, start_date=None):
# #         df = self.get_cashflow(start_date)
# #         return cashflow_to_history(df)
    
# #     def buy(self, size, t=None):
# #         try:
# #             response = order(self.api_key, self.api_secret, 'BUY', 'MARKET', 0, size)
# #             response.raise_for_status()
# #         except RequestException as e:
# #             print(e)
# #             print(response)
# #             response = None
        
# #         return response.json()
    
# #     def sell(self, size, t=None):
# #         try:
# #             response = order(self.api_key, self.api_secret, 'SELL', 'MARKET', 0, size)
# #             response.raise_for_status()
# #         except RequestException as e:
# #             print(e)
# #             print(response)
# #             response = None
        
# #         return response.json()