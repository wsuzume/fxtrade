import warnings

import numpy as np
import pandas as pd

from datetime import datetime
from glob import glob
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from .api import ChartAPI
from .dirmap import Directory, DirMap
from .timeseries import merge, down_sampling, select, normalized_timeindex, get_first_timestamp, to_timedelta

def standardize(df: pd.DataFrame, scaler: float=None, log=False):
    df_crop = df[['open', 'close', 'high', 'low', 'volume']].copy()
    
    if scaler is not None:
        df_crop = df_crop / scaler
    
    if log:
        return df_crop.apply(np.log10)
    
    return df_crop

# interpolate したレコードは timestamp が NaN になるようにしている
def normalize(df: pd.DataFrame, interval: pd.Timedelta,
              ascending: bool = False,
              interpolate_columns: List[str]=['open', 'close', 'high', 'low', 'volume']) -> pd.DataFrame:
    df = df.copy()
    b = df.index[0]
    end = df.index[-1]
    
    begin = get_first_timestamp(b, interval)
    delta = to_timedelta(interval)
    
    timeindex = set(normalized_timeindex(begin, end, delta))
    idx = timeindex - set(df.index)
    
    for i in sorted(list(idx)):
        df.loc[i] = np.nan
    
    df = df.sort_index()
    df[interpolate_columns] = df[interpolate_columns].interpolate()
    
    if not ascending:
        df = df.sort_index(ascending=ascending)
    
    return df


def default_loader(chart, key):
    path = chart.dirmap[key].last()
    if path is None:
        return chart.api.empty
    chart.dfs[key] = pd.read_csv(path, index_col=0)
    return chart.dfs[key]

class Chart:
    def __init__(self,
                 ticker: str,
                 api: Type[ChartAPI],
                 data_dir: Optional[Union[str, Path]]=None,
                 calc_geostats: bool=False
                ):
        self.ticker = ticker
        self.api = api
        self.dirmap = DirMap(name=ticker, root_dir=data_dir)
        self.dfs = {}
        
        for key in self.api.default_crange_intervals.keys():
            self.dirmap.add_branch(key)
            self.dfs[key] = self.api.empty
    
    def __getitem__(self, key):
        return self.dfs[key]
    
    def download(self, key: str):
        crange, interval = self.api.default_crange_intervals[key]
        df = self.api.download(ticker=self.ticker,
                               crange=crange,
                               interval=interval)
        return df
    
    def update(self, key: str, merge_function=merge):
        self.dfs[key] = merge_function(self.dfs[key], self.download(key))
    
    def save(self, key: str, name=None, scope='day'):
        if name is None:
            name = 'chart.csv'
        path = self.dirmap[key].now(name, scope)
        self.dfs[key].to_csv(path, index=True)
    
    def load(self, key: str, loader=default_loader):
        return loader(self, key)
    
    def down_sampling(self, key: str, sampling_interval: str, update=False):
        df = down_sampling(self.dfs[key], sampling_interval)
        if update:
            self.dfs[key] = df
        return df
    
    def select(self, key: str,
           year: Optional[int]=None,
           month: Optional[int]=None,
           day: Optional[int]=None,
           hour: Optional[int]=None,
           minute: Optional[int]=None,
           second: Optional[int]=None,
           update: bool=False
          ):
        
        df = select(self.dfs[key], year, month, day, hour, minute, second)
        if update:
            self.dfs[key] = df
        
        return df
    
#     def normalize(self, ascending=False):
#         for interval, df in self.dfs.items():
#             self.dfs[interval] = normalize(df, interval=interval)
        
#         return self.dfs
    
#     def standardize(self, scaler: float, mode: str='log'):
#         if self.scaler is not None:
#             raise ValueError("this chart is already standardized")
        
#         self.scaler = scaler
#         self.mode = mode
        
#         for interval, df in self.dfs.items():
#             self.dfs[interval] = standardize(df, scaler=self.scaler, mode=self.mode)
            
#         return self.dfs
    
#     def get_train_data(self, interval: str, end: Union[int, pd.Timestamp]=365):
#         if isinstance(end, pd.Timestamp):
#             idx = pd.Series(self.dfs[interval].index).apply(lambda x: x < end)
#             return self.dfs[interval].loc[idx.values]
        
#         elif isinstance(end, int):
#             validate_result = validate_index(self.dfs[interval])
#             ascending = validate_result['ascending']

#             if ascending:
#                 return self.dfs[interval].iloc[:end]
#             else:
#                 return self.dfs[interval].iloc[end:]
        
#         raise ValueError(f"unrecognized type end: {type(end)}")
    
#     def stream(self, interval: str, start: Union[int, pd.Timestamp]=0, fast_mode=True):
#         if isinstance(start, pd.Timestamp):
#             idx = pd.Series(self.dfs[interval].index).apply(lambda x: x >= start)
#             df = self.dfs[interval].loc[idx.values].sort_index(ascending=True)
#         elif isinstance(start, int):
#             validate_result = validate_index(self.dfs[interval])
#             ascending = validate_result['ascending']
            
#             if ascending:
#                 df = self.dfs[interval].iloc[start:]
#             else:
#                 df = self.dfs[interval].sort_index(ascending=True).iloc[start:]
        
#         if fast_mode:
#             return df.itertuples()
#         else:
#             return df.iterrows()
    
#     def now(self, interval: str, ascending: bool=True):
#         df = self.api.get_ticker(self.ticker, interval=interval, now=True)
        
#         if self.scaler is not None:
#             df = standardize(df, scaler=self.scaler, mode=self.mode)
#         if not ascending:
#             df = df.sort_index(ascending=ascending)
        
#         return df