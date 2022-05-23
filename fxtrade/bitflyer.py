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

import settings

from trade import Transfer, Trade

def build_headers(api_key: str, api_secret: str, method: str, endpoint: str, body: str='') -> dict:
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

def get_ticker(product_code='btc_jpy'):
    base_url = 'https://api.bitflyer.com'
    endpoint = '/v1/ticker'
    
    params = {
        "product_code": product_code,
    }
    
    return send_request(base_url, endpoint, params=params)

def get_trading_commision(api_key, api_secret, product_code):
    base_url = 'https://api.bitflyer.com'
    endpoint = '/v1/me/gettradingcommission'
    
    params = {
        "product_code": product_code,
    }

    return send_request(base_url, endpoint, method='GET', params=params, api_key=api_key, api_secret=api_secret)

def get_child_orders(api_key, api_secret, product_code='btc_jpy'):
    base_url = 'https://api.bitflyer.com'
    endpoint = '/v1/me/getchildorders'
    
    params = {
        "product_code": product_code,
        "count": str(100),
    }

    return send_request(base_url, endpoint, method='GET', params=params, api_key=api_key, api_secret=api_secret)

def order(side: str, order_type: str, price: int, size: float, expire: int=1000):
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
        "price": price,  # 価格指定
        "size": size,  # 注文数量
        "minute_to_expire": expire,  # 期限切れまでの時間（分）
        "time_in_force": 'GTC'  # GTC発注
    }

    body = json.dumps(body)
    
    return send_request(base_url, endpoint, method='POST', body=body, api_key=api_key, api_secret=api_secret)
    

def order_cancel(self):
    base_url = 'https://api.bitflyer.com'
    endpoint = "/v1/me/cancelchildorder"

    body = {
        "product_code": 'btc_jpy',
        "child_order_acceptance_id": "JRF20150707-033333-099999"
    }

    body = json.dumps(body)
    headers = self.header('POST', endpoint=endpoint, body=body)

    response = requests.post(base_url + endpoint, data=body, headers=headers)
    return response.status_code

def all_order_cancel():
    base_url = 'https://api.bitflyer.com'
    endpoint = "/v1/me/cancelallchildorders"

    body = {
        "product_code": 'btc_jpy'
    }

    body = json.dumps(body)
    headers = self.header('POST', endpoint=endpoint, body=body)

    response = requests.post(base_url + endpoint, data=body, headers=headers)
    return response.status_code

class BitflyerAPI:
    def __init__(self, api_key, api_secret, product_code='btc_jpy'):
        self.api_key = api_key
        self.api_secret = api_secret
        self.product_code = product_code
    
    def build_headers(self, method: str, endpoint: str, body: str=''):
        return build_headers(self.api_key, self.api_secret, method, endpoint, body)
    
    def get_balance(self):
        try:
            response = get_balance(self.api_key, self.api_secret)
            response.raise_for_status()
        except RequestException as e: 
            print(e)
            reponse = None
        return response.json()
    
    def get_balance_history(self, currency_code='JPY'):
        try:
            response = get_balance_history(self.api_key, self.api_secret, currency_code=currency_code)
            response.raise_for_status()
        except RequestException as e:
            print(e)
            response = None
        return response.json()
    
    def get_ticker(self):
        try:
            response = get_ticker(self.product_code)
            response.raise_for_status()
        except RequestException as e:
            print(e)
            response = None
        return response.json()
    
    def get_trading_commision(self):
        try:
            response = get_trading_commision(self.api_key, self.api_secret, self.product_code)
            response.raise_for_status()
        except RequestException as e:
            print(e)
            response = None
        return response.json()
    
    def get_child_orders(self):
        try:
            response = get_child_orders(self.api_key, self.api_secret, product_code=self.product_code)
            response.raise_for_status()
        except RequestException as e:
            print(e)
            response = None
        return response.json()
    
    def get_cash_flow(self):
        df_jpy = pd.DataFrame.from_dict(self.get_balance_history(currency_code='JPY'))
        df_btc = pd.DataFrame.from_dict(self.get_balance_history(currency_code='BTC'))
        
        df_jpy = df_jpy[['order_id', 'product_code', 'trade_date', 'trade_type', 'amount', 'quantity', 'commission', 'balance']]
        df_jpy.columns = ['order_id', 'product_code', 'trade_date', 'trade_type', 'X(t)', 'Y(t+dt)', 'commission_x', 'x(t)']
        df_jpy.set_index('order_id')
        
        df_btc = df_btc[['order_id', 'amount', 'quantity', 'commission', 'balance']]
        df_btc.columns = ['order_id', 'X(t+dt)', 'Y(t)', 'commission_y', 'y(t)']
        df_btc.set_index('order_id')
        
        df_all = pd.merge(df_jpy, df_btc, left_on='order_id', right_on='order_id', how='outer')
        
        df_all = df_all.dropna(subset=['trade_type', 'trade_date'])
        df_all['trade_date'] = df_all['trade_date'].apply(lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S.%f'))
        
        return df_all[['order_id', 'product_code', 'trade_date', 'trade_type',
                       'x(t)', 'y(t)', 'X(t)', 'Y(t)', 'X(t+dt)', 'Y(t+dt)', 'commission_x', 'commission_y']].copy()
    
    def get_trade_history(self):
        #df_balance = pd.DataFrame.from_dict(self.get_balance_history())
        #df_order = pd.DataFrame.from_dict(self.get_child_orders())
        df = self.get_cash_flow()
        
        #df = pd.merge(df_balance.drop(['id'], axis=1),
        #              df_order.drop(['id', 'product_code', 'price'], axis=1),
        #              left_on='order_id', right_on='child_order_id')
        
        df['parsed_trade_date'] = df['trade_date'].apply(lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S.%f'))
        
        columns = [
            'parsed_trade_date',
            'trade_date',
            'order_id',
            'product_code',
            'currency_code',
            'trade_type',
            'quantity',
            'amount',
            'price',
            'commission',
            'balance',
        ]

        return df[columns].copy()
    
    def get_trade_list(self, begin=None):
        df_cash_flow = self.get_cash_flow()
        #df_trades = self.get_trade_history()
        
        cash_flows = []
        trades = []
        for idx, row in df_cash_flow.iterrows():
            if row['trade_type'] not in { 'BUY', 'SELL' }:
                t = pd.Timestamp(datetime.strptime(row['trade_date'], '%Y-%m-%dT%H:%M:%S.%f'))
                cash_flows.append(Transfer(Fraction(row['amount']), row['currency_code'], t))
            else:
                stock = row['product_code']
                amount = Fraction(abs(row['amount']))
                quantity = Fraction(row['quantity'])

                if row['trade_type'] == 'BUY':
                    trades.append(Trade.buy(stock, y=quantity, ry=amount / quantity, t=row['parsed_trade_date']))
                elif row['trade_type'] == 'SELL':
                    trades.append(Trade.sell(stock, y=quantity, ry=amount / quantity, t=row['parsed_trade_date']))
                else:
                    raise ValueError('hoge')

        all_flows = sorted(cash_flows + trades, key=lambda x: x.t)

        if begin is not None:
            all_flows = list(filter(lambda x: x.t >= begin, all_flows))
        
        return all_flows