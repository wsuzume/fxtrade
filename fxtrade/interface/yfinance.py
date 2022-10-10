import json
import requests
import pandas as pd
import warnings

from datetime import datetime

from ..api import ChartAPI
from ..timeseries import year_sections, month_sections, day_sections

# chart_range ... 1d, 5d, 1mo, 3mo, 6mo, 1y, 5y, 10y, ytd, max
# interval ... 1m, 5m, 15m, 1d, 1wk, 1mo
# 可能な最大の組み合わせ
# '5d', '1m'
# '1mo', '15m'
# '10y', '1d'
def get_ticker(x_api_key, ticker='BTC-JPY', chart_range='10y', interval='1d'):
    url = f'https://yfapi.net/v8/finance/chart/{ticker}'

    headers = {
        'x-api-key': x_api_key
    }
    
    querystring = {
        'range': chart_range,
        'region': 'JP',
        'interval': interval,
        'lang': 'en',
        'events': 'div%2Csplit',
    }
    
    return requests.request("GET", url, headers=headers, params=querystring)

def response_to_dataframe(response):
    res = json.loads(response.text)
    
    data = zip(res['chart']['result'][0]['timestamp'],
               res['chart']['result'][0]['indicators']['quote'][0]['open'],
               res['chart']['result'][0]['indicators']['quote'][0]['close'],
               res['chart']['result'][0]['indicators']['quote'][0]['high'],
               res['chart']['result'][0]['indicators']['quote'][0]['low'],
               res['chart']['result'][0]['indicators']['quote'][0]['volume'],
              )

    df = pd.DataFrame(data, columns=['timestamp', 'open', 'close', 'high', 'low', 'volume'])
    
    df['Date'] = df['timestamp'].apply(datetime.fromtimestamp)
    df = df.set_index('Date')
    
    return df

class YahooFinanceAPI(ChartAPI):
    @staticmethod
    def make_ticker(from_code, to_code):
        return f"{from_code.upper()}-{to_code.upper()}"
    
    @staticmethod
    def make_currency_pair(pair):
        return f"{pair.terminal}-{pair.initial}"
        
    def __init__(self, api_key):
        self.api_key = api_key
        
    @property
    def tickers(self):
        return ['USD-JPY', 'BTC-JPY']
    
    @property
    def cranges(self):
        return ['1d', '5d', '1mo', '3mo', '6mo', '1y', '5y', '10y', 'ytd', 'max']
    
    @property
    def intervals(self):
        return ['1m', '5m', '15m', '1d', '1wk', '1mo']

    @property
    def max_cranges(self):
        return {
            '1d': '10y',
            '15m': '1mo',
            '1m': '5d',
        }
    
    @property
    def default_crange_interval(self):
        return '1mo-15m'

    @property
    def default_crange_intervals(self):
        return {
            '10y-1d': ('10y', '1d'),
            '1mo-15m': ('1mo', '15m'),
            '5d-1m': ('5d', '1m'),
        }
    
    @property
    def default_timestamp_filter(self):
        return {
            '10y-1d': lambda x: (x.hour == 0) and (x.minute == 0) \
                                and (x.second == 0) and (x.nanosecond == 0),
            '1mo-15m': lambda x: (x.minute % 15 == 0) \
                                and (x.second == 0) and (x.nanosecond == 0),
            '5d-1m': lambda x: (x.second == 0) and (x.nanosecond == 0),
        }
    
    @property
    def default_save_fstring(self):
        return {
            '10y-1d': '%Y.csv',
            '1mo-15m': '%Y-%m.csv',
            '5d-1m': '%Y-%m-%d.csv',
        }
    
    @property
    def default_save_iterator(self):
        return {
            '10y-1d': year_sections,
            '1mo-15m': month_sections,
            '5d-1m': day_sections,
        }
    
    @property
    def empty(self):
        return pd.DataFrame([], columns=['timestamp', 'open', 'close', 'high', 'low', 'volume'])
    
    def download(self, ticker, crange, interval, t=None, as_dataframe=True):
        if t is not None:
            warnings.warn(UserWarning("specifying the time is not supported. t must be None."))
        
        if ticker not in self.tickers:
            raise ValueError(f"ticker '{ticker}' not in {self.tickers}")
        if crange not in self.cranges:
            raise ValueError(f"crange '{crange}' not in {self.cranges}")
        if interval not in self.intervals:
            raise ValueError(f"interval '{interval}' not in {self.intervals}")

        response = get_ticker(self.api_key,
                              ticker=ticker,
                              chart_range=crange,
                              interval=interval)
        response.raise_for_status()
        
        if not as_dataframe:
            return response
            
        return response_to_dataframe(response)