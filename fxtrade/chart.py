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

def standardize(df: pd.DataFrame):
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("df.index must be type of pandas.DatetimeIndex")
        
    columns = ['timestamp', 'open', 'close', 'high', 'low', 'volume']
    
    return df[columns].copy()

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

def read_csv(path):
    return pd.read_csv(path, index_col=0, parse_dates=True)

def default_merge_function(df_prev, df):
    #return pd.concat([df1, df2], axis=0)
    return merge(df_prev, df)
    
def default_load_function(chart, key):
    paths = chart.dirmap[key].glob()
    if len(paths) == 0:
        raise FileNotFoundError(f"No file to read in '{chart.dirmap[key]}'")

    dfs = []
    for path in paths:
        dfs.append(read_csv(path))

    df_ret = dfs[0]
    for df in dfs[1:]:
        df_ret = default_merge_function(df_ret, df)

    return df_ret.sort_index()

class Chart:
    def __init__(self,
                 ticker: str,
                 api: Type[ChartAPI],
                 data_dir: Optional[Union[str, Path]]=None,
                ):
        self.ticker = ticker
        self.api = api
        self.dirmap = DirMap(root_dir=Path(data_dir) / ticker)
        self.dfs = {}
        
        for key in self.api.default_crange_intervals.keys():
            self.dirmap.add_branch(key)
            self.dfs[key] = self.api.empty
    
    def __getitem__(self, key):
        return self.dfs[key]
    
    def _download(self, key: str):
        crange, interval = self.api.default_crange_intervals[key]
        df = self.api.download(ticker=self.ticker,
                               crange=crange,
                               interval=interval)
        return standardize(df)
    
    def _download_all(self):
        ret = {}
        for key in self.api.default_crange_intervals.keys():
            ret[key] = self.download(key)
        return ret
    
    def download(self, key: str=None):
        if key is None:
            return self._download_all()
        return self._download(key)
    
    def _update(self, key: str, merge_function=merge):
        self.dfs[key] = self.download(key)
        #self.dfs[key] = merge_function(self.dfs[key], self.download(key))
        return self.dfs[key]
    
    def _update_all(self, merge_function=merge):
        ret = {}
        for key in self.api.default_crange_intervals.keys():
            ret[key] = self._update(key)
        return ret
    
    def update(self, key: str=None, merge_function=merge):
        if key is None:
            return self._update_all(merge_function)
        return self._update(key, merge_function)
    
    def _save(self, key: str, merge_function=default_merge_function):
        save_dir = self.dirmap[key]
        save_dir.ensure()
        
        fstring = self.api.default_save_fstring[key]
        sections = self.api.default_save_iterator[key]
        
        df = self.dfs[key]
        
        for begin, end in sections(df.index[0], df.index[-1]):
            save_name = begin.strftime(fstring)
            path = save_dir.path / save_name
            
            df_prev = read_csv(path) if path.exists() else None
            df_part = df[(df.index >= begin) & (df.index < end)]
            
            if df_prev is not None:
                df_part = merge_function(df_prev, df_part)
            
            df_part.to_csv(path, index=True)
        
        return save_dir
        
    def _save_all(self):
        ret = {}
        for key in self.dfs.keys():
            ret[key] = self._save(key)
            
        return ret
    
    def save(self, key: str=None):
        if key is None:
            return self._save_all()
        return self._save(key)
    
    def _load(self, key: str, load_function=default_load_function):
        if not self.dirmap[key].exists():
            raise FileNotFoundError(f"Directory not found '{self.dirmap[key]}'")
            
        self.dfs[key] = load_function(self, key)
        return self.dfs[key]
    
    def _load_all(self):
        for key in self.api.default_crange_intervals.keys():
            if self.dirmap[key].exists():
                self.dfs[key] = self._load(key)
        return self.dfs
    
    def load(self, key: str=None):
        if key is None:
            return self._load_all()
        return self._load(key)
    
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
    
