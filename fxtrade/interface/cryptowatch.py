import json
import requests
import pandas as pd
import warnings

from datetime import datetime
from typing import Union, Optional

from ..api import CodePair, CrangePeriod, ChartAPI

# from ..timeseries import year_sections, month_sections, day_sections

def get_chart(api_key, market, code_pair, chart_range, period):
    headers = {
        "X-CW-API-KEY": api_key,
    }

    query = {
        "periods": period,
    }

    url = f"https://api.cryptowat.ch/markets/{market}/{code_pair}/ohlc"

    return requests.request("GET", url, headers=headers, params=query)

def response_to_dataframe(response):
    columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'quotevolume']
    new_columns = ['timestamp', 'open', 'close', 'high', 'low', 'volume']
    
    resp = response.json()
    
    ret = {}
    for k, table in resp['result'].items():
        df = pd.DataFrame(table, columns=columns)

        df['Date'] = df['timestamp'].apply(datetime.fromtimestamp)
        df = df.set_index('Date')
        
        ret[k] = df[new_columns].copy()
    
    if len(ret) == 1:
        ret = list(ret.values())[0]
    
    return ret
    

class CryptowatchAPI(ChartAPI):
    # @staticmethod
    # def make_ticker(from_code, to_code):
    #     return f"{from_code.lower()}{to_code.lower()}"
    
    @staticmethod
    def make_code_pair_string(base: Union[str, CodePair], quote: Optional[str]=None) -> str:
        if isinstance(base, str):
            return f"{base.lower()}{quote.lower()}"
        elif isinstance(base, CodePair):
            return f"{base.base.lower()}{base.quote.lower()}"
        raise TypeError("unrecognized type arguments")
        
    def __init__(self, api_key, custom_crange_periods=None):
        self.api_key = api_key
        self._custom_crange_periods = custom_crange_periods
    
    def __repr__(self):
        return f"CryptowatchAPI(api_key='{self.api_key[:4]}...')"

    @property
    def code_pairs(self):
        return ['btcjpy']
    
    @property
    def cranges(self):
        return ['max']
    
    @property
    def periods(self):
        return ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d', '3d', '1w']

#     @property
#     def max_cranges(self):
#         return {
#             '1d': 'max',
#             '15m': 'max',
#             '1m': 'max',
#         }
    
    @property
    def default_crange_period(self):
        return CrangePeriod('max', '15m')

    def is_valid_crange_period(self, crange_period):
        return True
        if crange_period in self.default_crange_periods:
            return True
        
        if crange_period in self._custom_crange_periods:
            return True
        
        return False

    @property
    def default_crange_periods(self):
        return {
            'max-1d': ('10y', '1d'),
            'max-15m': ('1mo', '15m'),
            'max-1m': ('5d', '1m'),
        }
    
#     @property
#     def default_timestamp_filter(self):
#         return {
#             'max-1d': lambda x: (x.hour == 0) and (x.minute == 0) \
#                                 and (x.second == 0) and (x.nanosecond == 0),
#             'max-15m': lambda x: (x.minute % 15 == 0) \
#                                 and (x.second == 0) and (x.nanosecond == 0),
#             'max-1m': lambda x: (x.second == 0) and (x.nanosecond == 0),
#         }
    
#     @property
#     def default_save_fstring(self):
#         return {
#             'max-1d': '%Y.csv',
#             'max-15m': '%Y-%m.csv',
#             'max-1m': '%Y-%m-%d.csv',
#         }
    
#     @property
#     def default_save_iterator(self):
#         return {
#             'max-1d': year_sections,
#             'max-15m': month_sections,
#             'max-1m': day_sections,
#         }
    
    @property
    def empty(self):
        return pd.DataFrame([], columns=['timestamp', 'open', 'close', 'high', 'low', 'volume', 'quotevolume'])
    
    def period_to_seconds(self, period):
        table = {
            '1m': 60,
            '3m': 180,
            '5m': 300,
            '15m': 900,
            '30m': 1800,
            '1h': 3600,
            '2h': 7200,
            '4h': 14400,
            '6h': 21600,
            '12h': 43200,
            '1d': 86400,
            '3d': 259200,
            '1w': 604800,
        }

        return table[period]

    def download(self, code_pair, crange_period, t=None, as_dataframe=True):
        if t is not None:
            warnings.warn(UserWarning("specifying the time is not supported. t must be None."))
        
        code_pair = self.make_code_pair_string(code_pair)

        if code_pair not in self.code_pairs:
            raise ValueError(f"ticker '{code_pair}' not in {self.code_pairs}")
        # if crange not in self.cranges:
        #     raise ValueError(f"crange '{crange}' not in {self.cranges}")
        # if period not in self.periods:
        #     raise ValueError(f"interval '{period}' not in {self.periods}")

        response = get_chart(
            api_key=self.api_key,
            market='bitflyer',
            code_pair=code_pair,
            chart_range=crange_period.crange,
            period=self.period_to_seconds(crange_period.period)
        )

        response.raise_for_status()
        
        if not as_dataframe:
            return response
            
        return response_to_dataframe(response)