import json
import requests
import pandas as pd
import warnings

from datetime import datetime
from typing import Union, Optional

from ..api import CodePair, CRangePeriod, ChartAPI
from ..utils import focus

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
    @staticmethod
    def make_code_pair_string(base: Union[str, CodePair], quote: Optional[str]=None) -> str:
        if isinstance(base, str):
            return f"{base.lower()}{quote.lower()}"
        elif isinstance(base, CodePair):
            return f"{base.base.lower()}{base.quote.lower()}"
        raise TypeError("unrecognized type arguments")
        
    def __init__(self, api_key, custom_crange_periods=[]):
        self.api_key = api_key
        self._custom_crange_periods = [ crange_period.copy() for crange_period in custom_crange_periods ]
    
    def __repr__(self):
        return f"CryptowatchAPI(api_key='{self.api_key[:4]}...')"

    def freeze(self):
        return CryptowatchAPI(api_key='[frozen]', custom_crange_periods=self._custom_crange_periods)

    @property
    def code_pairs(self):
        return [CodePair('BTC', 'JPY')]
    
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
        return CRangePeriod('max', '15m')

    @property
    def default_crange_periods(self):
        return [
            CRangePeriod('max', '1h'),
            CRangePeriod('max', '15m'),
            CRangePeriod('max', '1m'),
        ]

    @property
    def crange_periods(self):
        return sorted(list(set(self.default_crange_periods + self._custom_crange_periods)))

    def is_valid_crange_period(self, crange_period):
        return crange_period in self.crange_periods

    # @property
    # def default_crange_periods(self):
    #     return {
    #         'max-1d': ('10y', '1d'),
    #         'max-15m': ('1mo', '15m'),
    #         'max-1m': ('5d', '1m'),
    #     }
    
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

    def download(self, code_pair, crange_period=None, t=None, as_dataframe=True):
        """
        t ... ignored if as_dataframe is False
        """
        if code_pair not in self.code_pairs:
            raise ValueError(f"ticker '{code_pair}' not in {self.code_pairs}")

        code_pair = self.make_code_pair_string(code_pair)
        # if crange not in self.cranges:
        #     raise ValueError(f"crange '{crange}' not in {self.cranges}")
        # if period not in self.periods:
        #     raise ValueError(f"interval '{period}' not in {self.periods}")

        if crange_period is None:
            crange_period = self.default_crange_period

        response = get_chart(
            api_key=self.api_key,
            market='bitflyer',
            code_pair=code_pair,
            chart_range=crange_period.crange.s,
            period=crange_period.period.seconds
        )

        response.raise_for_status()
        
        if not as_dataframe:
            return response
        
        df = response_to_dataframe(response)
        return focus(df, t)