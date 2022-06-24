import pandas as pd

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union, Mapping

from .api import ChartAPI

class ChartEmulatorAPI:
    def __init__(self,
                 api: Type[ChartAPI],
                 dfs: Mapping[str, pd.DataFrame],
                 root_dir: Path,
                 trace_real: bool=True,
                 seed = None,
                ):
        self.api = api
        self.dfs = deepcopy(dfs)
        
        # TODO: dirmap つくる
        self.root_dir = root_dir
        
        self.trace_real = trace_real
        self.seed = seed
        
        # TODO: 擬似データを保存して dfs をクリアする
        pass
     
    @property
    def tickers(self):
        return self.api.tickers
    
    @property
    def cranges(self):
        return self.api.cranges
    
    @property
    def intervals(self):
        return self.api.intervals
    
    @property
    def max_crange(self, interval):
        return self.api.max_crange
    
    @property
    def default_crange_intervals(self):
        return self.api.default_crange_intervals
    
    @property
    def default_timestamp_filter(self):
        return self.api.default_timestamp_filter
    
    @property
    def default_save_fstring(self):
        return self.api.default_save_fstring
    
    @property
    def default_save_iterator(self):
        return self.api.default_save_iterator
    
    @property
    def empty(self):
        return self.api.empty
    
    @property
    def now(self):
        return self.api.now
    
    @property
    def maxlong(self):
        return self.api.maxlong
    
    def download(self, ticker, crange, interval, t=None, as_dataframe=True):
        if ticker not in self.tickers:
            raise ValueError(f"ticker '{ticker}' not in {self.tickers}")
        if crange not in self.cranges:
            raise ValueError(f"crange '{crange}' not in {self.cranges}")
        if interval not in self.intervals:
            raise ValueError(f"interval '{interval}' not in {self.intervals}")
        
        crange_interval = '-'.join([crange, interval])
        
        if crange_interval not in self.dfs:
            raise ValueError(f"'{crange_interval}' not in dfs")

        # 過去のデータをロードするようにつくりなおす
            
        df = self.dfs[crange_interval]
        
        if t is not None:
            df = df[df.index <= t]
            
        return df