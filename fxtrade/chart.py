import warnings

import numpy as np
import pandas as pd

from copy import deepcopy
from datetime import datetime
from io import StringIO
from glob import glob
from pathlib import Path
from typing import get_args, Any, Callable, Dict, List, Optional, Tuple, Type, Union, Iterable, Mapping

# from . import dirmap

# from .analysis import log10
from .api import ChartAPI
from .core import is_instance_list
# from .dirmap import DirMap
from .stock import CodePair
# from .timeseries import merge, down_sampling, select, \
#                         normalized_timeindex, get_first_timestamp, \
#                         to_timedelta

# def standardize(df: pd.DataFrame):
#     """
#     使用するカラムを選択する
#     """
#     if not isinstance(df.index, pd.DatetimeIndex):
#         raise TypeError("df.index must be type of pandas.DatetimeIndex")
        
#     columns = ['timestamp', 'open', 'close', 'high', 'low', 'volume']
    
#     return df[columns].copy()

# # interpolate したレコードは timestamp が NaN になるようにしている
# def normalize(df: pd.DataFrame, interval: pd.Timedelta,
#               ascending: bool = False,
#               interpolate_columns: List[str]=['open', 'close', 'high', 'low', 'volume']) -> pd.DataFrame:
#     """
#     NaN で計算が滞らないように線形補間する
#     """
#     df = df.copy()
#     b = df.index[0]
#     end = df.index[-1]
    
#     begin = get_first_timestamp(b, interval)
#     delta = to_timedelta(interval)
    
#     timeindex = set(normalized_timeindex(begin, end, delta))
#     idx = timeindex - set(df.index)
    
#     for i in sorted(list(idx)):
#         df.loc[i] = np.nan
    
#     df = df.sort_index()
#     df[interpolate_columns] = df[interpolate_columns].interpolate()
    
#     if not ascending:
#         df = df.sort_index(ascending=ascending)
    
#     return df

# def default_read_function(path: Union[str, Path]) -> pd.DataFrame:
#     return pd.read_csv(path, index_col=0, parse_dates=True)

# def default_merge_function(df_prev: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
#     return merge(df_prev, df)

# def default_glob_function(dir_path: Union[str, Path]) -> List[str]:
#     return sorted(list(Path(dir_path).glob('*.csv')))

# def default_restore_function(paths: Iterable[Union[str, Path]]) -> pd.DataFrame:
#     dfs = []
#     for path in paths:
#         dfs.append(default_read_function(path))

#     df_ret = dfs[0]
#     for df in dfs[1:]:
#         df_ret = default_merge_function(df_ret, df)

#     return df_ret.sort_index()

# def default_save_function(
#                 df: pd.DataFrame,
#                 dir_path: Union[str, Path],
#                 sections: Callable[[datetime, datetime], Iterable[Tuple[datetime, datetime]]],
#                 format_string: str,
#                 timestamp_filter: Callable[[datetime], bool]=None
#                 ) -> Path:
#     save_dir = Path(dir_path)
#     dirmap.ensure(save_dir)

#     if len(df) == 0:
#         warnings.warn(UserWarning(f"dataframe size is zero: no data to save."))
#         return save_dir
    
#     # 期間ごとに小分けにしてイテレート
#     for begin, end in sections(df.index[0], df.index[-1]):
#         save_name = begin.strftime(format_string)
#         path = save_dir / save_name
        
#         # 小分けにしたデータフレーム
#         df_part = df[(df.index >= begin) & (df.index < end)]

#         # 過去に同期間が保存されていれば読み込んでマージ
#         if path.exists():
#             df_prev = default_read_function(path)
#             df_part = default_merge_function(df_prev, df_part)
        
#         # 保存するデータを選択する
#         if timestamp_filter is not None:
#             save_idx = pd.Series(df_part.index).apply(
#                             timestamp_filter
#                         )
#             df_part = df_part.loc[save_idx.values]
        
#         # 保存する
#         df_part.to_csv(path, index=True)
    
#     return save_dir

class Board:
    def __init__(self,
                 code_pair: str,
                 crange_period: str,
                 api: Type[ChartAPI],
                 df: pd.DataFrame=None,
                 refresh_limit=None):
        self.code_pair = code_pair
        self.crange_period = crange_period
        self.api = api
        self.df = df if df is not None else self.api.empty
        self._refresh_limit = refresh_limit
    
    def __repr__(self):
        return self.dumps()

    def dump(self, f, indent=2, nest=1):
        tab = " " * indent * nest
        last_tab = " " * (indent * (nest - 1))
        f.write(f"Board(code_pair='{self.code_pair}', crange_period='{self.crange_period}',\n")
        f.write(f"{tab}api={self.api},\n")
        f.write(f"{tab}refresh_limit={self.refresh_limit},\n")
        f.write(f"{tab}first_updated={self.first_updated},\n")
        f.write(f"{tab}last_updated={self.last_updated},\n")
        f.write(f"{last_tab})")

    def dumps(self, indent=4):
        with StringIO() as f:
            self.dump(f, indent=indent)
            ret = f.getvalue()
        return ret

#     def __repr__(self):
#         return f"Board('{self.code_pair}', '{self.crange_interval}')"

#     def copy(self, api=None):
#         if api is None:
#             api = self.api
#         return Board(code_pair=self.code_pair,
#                      crange_interval=self.crange_interval,
#                      api=api,
#                      df=self.df.copy(),
#                      refresh_limit=self.refresh_limit)

    @property
    def refresh_limit(self):
        return self._refresh_limit
    
#     @refresh_limit.setter
#     def refresh_limit(self, dt):
#         self._refresh_limit = dt

    @property
    def first_updated(self):
        if len(self.df) == 0:
            return None
        
        return self.df.index[0]

    @property
    def last_updated(self):
        if len(self.df) == 0:
            return None
        
        return self.df.index[-1]

#     def should_be_updated(self, refresh_limit=None):
#         if refresh_limit is None:
#             refresh_limit = self.refresh_limit

#         if refresh_limit is None:
#             return True
#         if self.last_updated is None:
#             return True
        
#         now = pd.Timestamp.now()
#         if (now - self.last_updated) > refresh_limit:
#             return True
        
#         return False
    
#     def flush(self):
#         self.df = self.api.empty
#         return self.df
    
#     def download(self, t=None):
#         crange, interval = self.crange_interval.split('-')
#         df = self.api.download(code_pair=self.code_pair,
#                                crange=crange,
#                                interval=interval,
#                                t=t)
        
#         if t is not None:
#             self.df = self.df[self.df.index <= t].copy()

#         return standardize(df)
    
#     def update(self, t=None, df: pd.DataFrame=None, merge_function=None):
#         if merge_function is None:
#             merge_function = default_merge_function

#         if df is None:
#             df = self.download(t=t)
#         self.df = merge_function(self.df, df)
#         return self

#     def sync(self, dir_path, t=None, update=True, refresh_limit=None, glob_function=None, restore_function=None, merge_function=None):
#         if glob_function is None:
#             glob_function = default_glob_function
#         if restore_function is None:
#             restore_function = default_restore_function
#         if merge_function is None:
#             merge_function = default_merge_function

#         load_dir = Path(dir_path)
#         if load_dir.exists():
#             paths = glob_function(load_dir)
#             if len(paths) != 0:
#                 # ディレクトリが存在し、かつ読み込むべきファイルも存在する
#                 self.df = self.read(load_dir, t=t, glob_function=glob_function, restore_function=restore_function)
        
#         if not self.should_be_updated(refresh_limit):
#             return self

#         if update:
#             self.update(t=t, merge_function=merge_function)
#             self.save(dir_path)

#         return self

#     def read(self, dir_path, t=None, glob_function=None, restore_function=None):
#         if glob_function is None:
#             glob_function = default_glob_function
#         if restore_function is None:
#             restore_function = default_restore_function

#         key = self.crange_interval
#         fmt = self.api.default_save_fstring[key]

#         if t is None:
#             f = lambda x: True
#             g = lambda idx: idx
#         elif isinstance(t, datetime):
#             f = lambda x: datetime.strptime(x.name, fmt) <= t
#             g = lambda idx: idx
#         elif is_instance_list(t, datetime, 2):
#             if t[1] is not None:
#                 f = lambda x: t[0] <= datetime.strptime(x.name, fmt)
#             else:
#                 f = lambda x: t[0] <= datetime.strptime(x.name, fmt) <= t[1]
#             g = lambda idx: list(filter(lambda x: x >= 0, [idx[0] - 1] + list(idx)))
#         else:
#             raise TypeError("t must be instance of datetime or Tuple[datetime, datetime]")

#         load_dir = Path(dir_path)
#         if not load_dir.exists():
#             raise FileNotFoundError(f"Directory not found '{load_dir}'")

#         paths = glob_function(load_dir)
#         if len(paths) == 0:
#             raise FileNotFoundError(f"No file to read in '{load_dir}'")

#         idx = g([ i for i, p in enumerate(paths) if f(p) ])

#         paths = [ paths[i] for i in idx ]
#         if len(paths) == 0:
#             raise FileNotFoundError(f"No files remained after applying time filter")

#         df = standardize(restore_function(paths))

#         if isinstance(t, datetime):
#             df = df[df.index <= t].copy()
#         elif is_instance_list(t, datetime, 2):
#             if t[1] is None:
#                 df = df[df.index >= t[0]].copy()
#             else:
#                 df = df[(df.index >= t[0]) & (df.index <= t[1])].copy()
        
#         return df

#     def load(self, dir_path, t=None, glob_function=None, restore_function=None):
#         self.df = self.read(dir_path, t, glob_function, restore_function)
#         return self

#     def save(self, dir_path, save_function=None):
#         if save_function is None:
#             save_function = default_save_function
 
#         key = self.crange_interval

#         return save_function(
#                     df=self.df,
#                     dir_path=dir_path,
#                     sections=self.api.default_save_iterator[key],
#                     format_string=self.api.default_save_fstring[key],
#                     timestamp_filter=self.api.default_timestamp_filter[key]
#                     )

#     # def down_sampling(self):
#     #     pass
    
#     # def normalize(self):
#     #     pass
    
#     # def select(self):
#     #     pass

# class LogChart:
#     def __init__(self, dfs):
#         self.dfs = dfs
    
#     def __getitem__(self, key):
#         return log10(self.dfs[key])

class Chart:
    def __init__(self,
                 api: Type[ChartAPI],
                 code_pair: CodePair,
                 data_dir: Union[str, Path],
                 crange_period: Union[str, Iterable[str]]=None
                ):
        self.api = api
        self.code_pair = code_pair.copy()
        self.data_dir = Path(data_dir)
        self.board = {}
        if crange_period is None:
            crange_period = [self.api.default_crange_period]
        for key in self._to_crange_period_list(crange_period):
            self.add(key, self.api)
    
    def __getitem__(self, key):
        return self.board[key]

    def __repr__(self):
        return self.dumps()

    def dump(self, f, indent=2, nest=1):
        tab = " " * indent * nest
        tabtab = " " * (indent * (nest + 1))
        last_tab = " " * (indent * (nest - 1))

        f.write(f"Chart(code_pair={self.code_pair},\n")
        f.write(f"{tab}api={self.api},\n")
        f.write(f"{tab}data_dir='{self.data_dir}',\n")
        f.write(f"{tab}crange_period={sorted(list(self.board.keys()))},\n")
        f.write(f"{tab}board={{\n")
        for key, board in self.board.items():
            f.write(f"{tabtab}'{key}': ")
            board.dump(f, indent=indent, nest=nest+2)
            f.write(f",\n")
        f.write(f"{tab}}}\n")
        f.write(f"{last_tab})")
    
    def dumps(self, indent=4):
        with StringIO() as f:
            self.dump(f, indent=indent)
            ret = f.getvalue()
        return ret

    def _to_crange_period_list(self, crange_period: Union[str, Iterable[str]]):
        if isinstance(crange_period, str):
            keys = [crange_period]
        elif is_instance_list(crange_period, str):
            keys = crange_period
        else:
            raise TypeError("crange_period must be instance of str or Iterable[str]")

        return keys
    
    def add(self, crange_period, api=None, refresh_limit=None):
        api = api if api is not None else self.api
        
        self.board[crange_period] = \
                            Board(
                                code_pair=self.api.make_code_pair_string(self.code_pair),
                                crange_period=crange_period,
                                api=api,
                                refresh_limit=refresh_limit
                            )
        
        return self

    
#     def copy(self, api=None, data_dir=None):
#         if api is None:
#             api = self.api
#         if data_dir is None:
#             data_dir = self.data_dir
        
#         chart = Chart(api, self.code_pair, data_dir, self.crange_interval)
#         for key, board in self.board.items():
#             chart.board[key] = board.copy(api=api)
        
#         return chart

#     def create_emulator(self, emulator_dir: Union[str, Path], data_dir: Union[str, Path]):
#         emulator_dir = Path(emulator_dir)
#         data_dir = Path(data_dir)

#         self.save(data_dir=emulator_dir)

#         api = ChartEmulatorAPI(self, emulator_dir)

#         return self.copy(api=api, data_dir=data_dir)

#     @property
#     def dfs(self):
#         return { k: v.df for k, v in self.board.items() }
        
    
#     def flush(self, crange_interval: Union[str, Iterable[str]]=None):
#         for key in self._to_crange_interval_list(crange_interval):
#             board = self.board[key]
#             board.flush()

#         return self

#     def download(self, crange_interval: Union[str, Iterable[str]]=None, t=None, data_dir=None):
#         data_dir = Path(data_dir) if data_dir is not None else self.data_dir
#         ret = {}
#         for key in self._to_crange_interval_list(crange_interval):
#             ret[key] = self.board[key].download(t)
        
#         return ret
    
#     def update(self, crange_interval: Union[str, Iterable[str]], data_dir=None):
#         data_dir = Path(data_dir) if data_dir is not None else self.data_dir
#         for key in self._to_crange_interval_list(crange_interval):
#             board = self.board[key]
#             dir_path = data_dir / board.code_pair / board.crange_interval
#             board.update(dir_path)
        
#         return self
    
#     def read(self, crange_interval: Union[str, Iterable[str]]=None, t: datetime=None, data_dir=None):
#         data_dir = Path(data_dir) if data_dir is not None else self.data_dir
#         ret = {}
#         for key in self._to_crange_interval_list(crange_interval):
#             board = self.board[key]
#             dir_path = data_dir / board.code_pair / board.crange_interval
#             ret[key] = board.read(dir_path, t)
        
#         return ret

#     def load(self, crange_interval: Union[str, Iterable[str]]=None, t: datetime=None, data_dir=None):
#         data_dir = Path(data_dir) if data_dir is not None else self.data_dir
#         for key in self._to_crange_interval_list(crange_interval):
#             board = self.board[key]
#             dir_path = data_dir / board.code_pair / board.crange_interval
#             self.board[key] = board.load(dir_path, t)
        
#         return self

#     def save(self, crange_interval: Union[str, Iterable[str]]=None, data_dir=None):
#         data_dir = Path(data_dir) if data_dir is not None else self.data_dir
#         for key in self._to_crange_interval_list(crange_interval):
#             board = self.board[key]
#             dir_path = data_dir / board.code_pair / board.crange_interval
#             board.save(dir_path)
        
#         return self
    
#     def sync(self, crange_interval: Union[str, Iterable[str]]=None, t=None, data_dir=None, update: bool=True, save: bool=True):
#         data_dir = Path(data_dir) if data_dir is not None else self.data_dir
#         for key in self._to_crange_interval_list(crange_interval):
#             board = self.board[key]
#             dir_path = data_dir / board.code_pair / board.crange_interval
#             dirmap.ensure(dir_path)
#             board.sync(dir_path, t=t, update=update)
        
#         return self

# class ChartEmulatorAPI(ChartAPI):
#     @staticmethod
#     def make_code_pair(pair):
#         return f"{pair.terminal}-{pair.initial}"
        
#     def __init__(self,
#                  chart: Chart,
#                  root_dir: Path=None,
#                 ):
#         self.api = chart.api
#         self.board = { k: v.copy() for k, v in chart.board.items() }
#         self.root_dir = Path(root_dir)

#         for board in chart.board.values():
#             dir_path = self.root_dir / board.code_pair / board.crange_interval
#             board.sync(dir_path, update=False)
     
#     @property
#     def code_pairs(self):
#         return self.api.code_pairs
    
#     @property
#     def cranges(self):
#         return self.api.cranges
    
#     @property
#     def intervals(self):
#         return self.api.intervals
    
#     @property
#     def max_cranges(self):
#         return self.api.max_cranges
    
#     @property
#     def default_crange_interval(self):
#         return '1mo-15m'

#     @property
#     def default_crange_intervals(self):
#         return self.api.default_crange_intervals
    
#     @property
#     def default_timestamp_filter(self):
#         return self.api.default_timestamp_filter
    
#     @property
#     def default_save_fstring(self):
#         return self.api.default_save_fstring
    
#     @property
#     def default_save_iterator(self):
#         return self.api.default_save_iterator
    
#     @property
#     def empty(self):
#         return self.api.empty

#     def download(self, code_pair, crange, interval, t=None, as_dataframe=True):
#         if not as_dataframe:
#             raise ValueError(f"as_dataframe must be True")

#         if code_pair not in self.code_pairs:
#             raise ValueError(f"code_pair '{code_pair}' not in {self.code_pairs}")
#         if crange not in self.cranges:
#             raise ValueError(f"crange '{crange}' not in {self.cranges}")
#         if interval not in self.intervals:
#             raise ValueError(f"interval '{interval}' not in {self.intervals}")
        
#         crange_interval = ChartEmulatorAPI.make_crange_interval(crange, interval)
        
#         if crange_interval not in self.board:
#             raise ValueError(f"'{crange_interval}' not in dfs")

#         # 過去のデータをロードするようにつくりなおす
        
#         df = self.board[crange_interval].df
        
#         if t is None:
#             pass
#         elif isinstance(t, datetime):
#             df = df[df.index <= t]
#         elif is_instance_list(t, datetime, 2):
#             if t[1] is None:
#                 df = df[df.index >= t[0]]
#             else:
#                 df = df[(df.index >= t[0]) & (df.index <= t[1])]
#         else:
#             TypeError(f"")
            
#         return df.copy()
