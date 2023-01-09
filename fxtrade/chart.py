import warnings

import numpy as np
import pandas as pd

from copy import deepcopy
from datetime import datetime
from io import StringIO
from glob import glob
from pathlib import Path
from types import EllipsisType
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union, Iterable, Mapping

# from .analysis import log10
from .api import CodePair, CrangePeriod, ChartAPI
from .core import type_checked, is_instance_list, is_instance_dict
# from .timeseries import merge, down_sampling, select, \
#                         normalized_timeindex, get_first_timestamp, \
#                         to_timedelta

from .helper import standardize

class Board:
    def __init__(self,
                 api: Type[ChartAPI],
                 code_pair: CodePair,
                 crange_period: CrangePeriod,
                 df: pd.DataFrame=None,
                 interval: Optional[datetime]=None):
        self.code_pair = type_checked(code_pair, CodePair).copy()
        self.crange_period = type_checked(crange_period, CrangePeriod).copy()
        self.api = type_checked(api, ChartAPI)

        self.df = df if df is not None else self.api.empty
        self._interval = interval
    
    def __repr__(self):
        return self.dumps()

    def dump(self, f, indent=2, nest=1):
        tab = " " * indent * nest
        last_tab = " " * (indent * (nest - 1))
        f.write(f"Board(api={self.api},\n")
        f.write(f"{tab}code_pair='{self.code_pair}',\n")
        f.write(f"{tab}crange_period='{self.crange_period}',\n")
        f.write(f"{tab}interval={self.interval},\n")
        f.write(f"{tab}first_updated={self.first_updated},\n")
        f.write(f"{tab}last_updated={self.last_updated},\n")
        f.write(f"{last_tab})")

    def dumps(self, indent=4):
        with StringIO() as f:
            self.dump(f, indent=indent)
            ret = f.getvalue()
        return ret

#     def copy(self, api=None):
#         if api is None:
#             api = self.api
#         return Board(code_pair=self.code_pair,
#                      crange_interval=self.crange_interval,
#                      api=api,
#                      df=self.df.copy(),
#                      interval=self.interval)

    @property
    def interval(self):
        return self._interval
    
#     @interval.setter
#     def interval(self, dt):
#         self._interval = dt

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

#     def should_be_updated(self, interval=None):
#         if interval is None:
#             interval = self.interval

#         if interval is None:
#             return True
#         if self.last_updated is None:
#             return True
        
#         now = pd.Timestamp.now()
#         if (now - self.last_updated) > interval:
#             return True
        
#         return False
    
#     def flush(self):
#         self.df = self.api.empty
#         return self.df
    
    def download(self, t=None):
        df = self.api.download(code_pair=self.code_pair,
                               crange_period=self.crange_period,
                               t=t)
        
        if t is not None:
            self.df = self.df[self.df.index <= t].copy()

        return standardize(df)
    
#     def update(self, t=None, df: pd.DataFrame=None, merge_function=None):
#         if merge_function is None:
#             merge_function = default_merge_function

#         if df is None:
#             df = self.download(t=t)
#         self.df = merge_function(self.df, df)
#         return self

#     def sync(self, dir_path, t=None, update=True, interval=None, glob_function=None, restore_function=None, merge_function=None):
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
        
#         if not self.should_be_updated(interval):
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
                 crange_period: Union[CrangePeriod, Iterable[CrangePeriod]]=None
                ):
        self.api = type_checked(api, ChartAPI)
        self.code_pair = self._to_code_pair(code_pair)
        self.data_dir = Path(data_dir)
        self.board = {}
        if crange_period is None:
            crange_period = [ self.api.default_crange_period ]
        for name, cp in self._make_crange_period_dict(crange_period).items():
            self.add(cp, name=name, api=self.api)
    
    def __getitem__(self, key):
        return self.board[key]

    def __repr__(self):
        return self.dumps()

    def dump(self, f, indent=2, nest=1):
        tab = " " * indent * nest
        tabtab = " " * (indent * (nest + 1))
        last_tab = " " * (indent * (nest - 1))

        f.write(f"Chart(api={self.api},\n")
        f.write(f"{tab}code_pair={self.code_pair},\n")
        f.write(f"{tab}data_dir='{self.data_dir}',\n")
        f.write(f"{tab}crange_period={list(self.board.keys())},\n")
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

    def _to_code_pair(self, code_pair: Union[str, CodePair]):
        if isinstance(code_pair, str):
            return self.api.code_pair_from_string(code_pair)
        elif isinstance(code_pair, CodePair):
            return code_pair.copy()
        raise TypeError(f"code_pair must be instance of {str} or {CodePair}")

    def _make_crange_period(self,
            crange_period: Union[str, CrangePeriod, EllipsisType],
            name: Optional[Union[str, CrangePeriod]]=None):
        if isinstance(name, CrangePeriod):
            if crange_period is not ...:
                raise ValueError(f"crange_period must be ... {EllipsisType} when name is instance of {CrangePeriod}.")
        if name is not None:
            if not isinstance(name, (str, CrangePeriod)):
                raise TypeError(f"name must be instance of {str} or {CrangePeriod} but actual type {type(name)}.")
            if crange_period is ...:
                crange_period = name
            else:
                # name is ignored
                pass

        if isinstance(crange_period, str):
            return self.api.crange_period_from_string(crange_period)
        elif isinstance(crange_period, CrangePeriod):
            return crange_period.copy()

        raise TypeError(f"crange_period must be instance of {str} or {CrangePeriod} but actual type {(type(crange_period))}.")

    def _make_crange_period_list(self,
            crange_period: Union[str, CrangePeriod,
                                Iterable[Union[str, CrangePeriod]]]):
        xs = crange_period
        if isinstance(xs, (str, CrangePeriod)):
            return [ self._make_crange_period(xs) ]
        elif is_instance_list(xs, (str, CrangePeriod)):
            return [ self._make_crange_period(x) for x in xs ]
        raise TypeError(f"crange_period must be instance of {str}, {CrangePeriod}, {Iterable[Union[str, CrangePeriod]]}.")

    def _make_crange_period_dict(self,
            crange_period: Union[str, CrangePeriod,
                                Iterable[Union[str, CrangePeriod]],
                                Mapping[str, Union[str, CrangePeriod]]]):
        xs = crange_period
        if isinstance(xs, (str, CrangePeriod)):
            return { xs: self._make_crange_period(xs) }
        elif is_instance_dict(xs, kt=(str, CrangePeriod), vt=(str, CrangePeriod, EllipsisType)):
            return { name: self._make_crange_period(crange_period, name=name) for name, crange_period in xs.items() }
        elif is_instance_list(crange_period, (str, CrangePeriod)):
            return { x: self._make_crange_period(x) for x in xs }
        raise TypeError(f"crange_period must be instance of {str}, {CrangePeriod}, {Iterable[Union[str, CrangePeriod]]}, or {Mapping[str, Union[str, CrangePeriod, EllipsisType]]}.")
        
    def add(self, crange_period: Union[str, CrangePeriod], name: Optional[str]=None, api=None, interval=None):
        api = api if api is not None else self.api
        crange_period = self._make_crange_period(crange_period)
        if name is None:
            name = crange_period
        else:
            name = type_checked(name, (str, CrangePeriod))

        if not api.is_valid_crange_period(crange_period):
            raise ValueError(f"invalid crange_period: '{crange_period}'")
        
        self.board[name] = \
            Board(
                api=api,
                code_pair=self.code_pair,
                crange_period=crange_period,
                interval=interval
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

    def download(self, crange_interval: Union[str, Iterable[str]]=None, t=None, data_dir=None):
        data_dir = Path(data_dir) if data_dir is not None else self.data_dir
        ret = {}
        for key in self._to_crange_interval_list(crange_interval):
            ret[key] = self.board[key].download(t)
        
        return ret
    
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

class ChartDummyAPI(ChartAPI):
    def __init__(self):
        pass

    def __repr__(self):
        return f"ChartDummyAPI()"

    @property
    def empty(self):
        return pd.DataFrame([], columns=['timestamp', 'open', 'close', 'high', 'low', 'volume', 'quotevolume'])
    
    @property
    def default_crange_period(self) -> str:
        return CrangePeriod('max', '15m')
    
    def is_valid_crange_period(self, crange_period: str) -> bool:
        table = {
            CrangePeriod('max', '1d'),
            CrangePeriod('max', '15m'),
            CrangePeriod('max', '1m'),
        }
        
        return crange_period in table

class ChartEmulatorAPI(ChartAPI):
    def __init__(self,
                 chart: Chart=None,
                 root_dir: Path=None,
                ):
        
        if chart is not None:
            self.api = chart.api
            self.board = { k: v.copy() for k, v in chart.board.items() }
            self.root_dir = Path(root_dir)

            for board in chart.board.values():
                dir_path = self.root_dir / board.code_pair / board.crange_interval
                board.sync(dir_path, update=False)
     
#     @property
#     def empty(self):
#         return self.api.empty

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
